from django.db.models import Avg
from django.shortcuts import render

# Create your views here.

from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from libraryMS.models import Author, Borrower, Book, BorrowingTransaction, Reservation, Review, Notification
from libraryMS.serializers import (
    NotificationSerializer,
    SignUpSerializer,
    AuthorSerializer,
    BorrowerSerializer,
    BookSerializer,
    BorrowingTransactionSerializer,
    ReservationSerializer,
    ReviewSerializer
)
from libraryMS.permissions import (
    IsAdmin,
    IsAuthor,
    IsOwnerOrReadOnly,
    CanReserveBook,
    CanBorrowBook,
    CanReviewBook,
    IsBorrower
)
from rest_framework.decorators import action
from rest_framework.response import Response


class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Author ViewSet
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        actionf = getattr(self, 'action', None)
        if actionf in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return super().get_permissions()


# Borrower ViewSet
class BorrowerViewSet(viewsets.ModelViewSet):
    queryset = Borrower.objects.all()
    serializer_class = BorrowerSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        actionf = getattr(self, 'action', None)
        if actionf in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return super().get_permissions()


# Book ViewSet
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # Filter books to show only those created by the logged-in author
        user = self.request.user
        # If the user is an author, show only their books
        if hasattr(user, 'author'):
            return Book.objects.filter(author=user.author)

        # If the user is a borrower, show all books
        if hasattr(user, 'borrower'):
            return Book.objects.all()

        return Book.objects.none()

    def perform_create(self, serializer):
        # Ensure the book is created by the logged-in author
        if hasattr(self.request.user, 'author'):
            serializer.save(author=self.request.user.author)
        else:
            raise PermissionDenied("Only authors can create books.")

    def destroy(self, request, *args, **kwargs):
        # Prevent authors from deleting books
        raise PermissionDenied("Authors cannot delete books.")

    def update(self, request, *args, **kwargs):
        # Prevent authors from updating certain fields
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check if the author is allowed to update this book
        if instance.author != request.user.author:
            raise PermissionDenied("You do not have permission to edit this book.")

        # Ensure fields like borrowed_by, reserved_by, and average_rating are not updated
        data = request.data
        if 'borrowed_by' in data or 'reserved_by' in data or 'average_rating' in data:
            raise PermissionDenied("You cannot update borrowed_by, reserved_by, or average_rating fields.")

        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Fetch reviews for a specific book"""
        book = self.get_object()
        reviews = Review.objects.filter(book=book)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        """Borrow a book if it is available"""
        book = self.get_object()
        borrower = self.request.user.borrower

        # Check if the book is already borrowed
        if book.borrowed_by:
            raise PermissionDenied("This book is currently borrowed by someone else.")

        # Check if the book is already reserved
        if book.reserved_by and book.reserved_by != borrower:
            raise PermissionDenied("This book is currently reserved by someone else.")

        # Check if the borrower already has 5 borrowed books
        active_borrowings_count = BorrowingTransaction.objects.filter(borrower=borrower, is_returned=False).count()
        if active_borrowings_count >= 5:
            raise PermissionDenied("You cannot borrow more than 5 books at a time.")

        if book.reserved_by == borrower:
            Reservation.objects.filter(book=book, borrower=borrower).delete()
            book.reserved_by = None

        # Create a new BorrowingTransaction
        borrowed_date = timezone.now()
        due_date = borrowed_date + timedelta(days=30)  # Due date is 30 days after borrowed date

        # Create the borrowing transaction
        BorrowingTransaction.objects.create(
            borrower=self.request.user.borrower,
            book=book,
            borrowed_date=borrowed_date,
            due_date=due_date,
            is_returned=False
        )

        # Mark the book as borrowed
        book.borrowed_by = self.request.user.borrower
        book.save()

        return Response({"message": "Book borrowed successfully!"}, status=status.HTTP_200_OK)


# Borrowing Transaction ViewSet
class BorrowingTransactionViewSet(viewsets.ModelViewSet):
    queryset = BorrowingTransaction.objects.all()
    serializer_class = BorrowingTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        borrower = user.borrower if hasattr(user, 'borrower') else None

        # Base queryset for the borrower
        queryset = BorrowingTransaction.objects.filter(borrower=borrower)

        # Get filter parameters
        filter_type = self.request.query_params.get('filter', None)

        if filter_type == 'previous':
            # Filter for previous transactions (books that have been returned)
            queryset = queryset.filter(is_returned=True)
        elif filter_type == 'current':
            # Filter for current borrowings (books that are still borrowed)
            queryset = queryset.filter(is_returned=False)
        elif filter_type == 'due_date':
            # Filter for books due in the future (books close to the due date)
            today = timezone.now().date()
            queryset = queryset.filter(is_returned=False, due_date__lte=today + timedelta(days=7))

        return queryset

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """Allow a borrower to return a book"""
        transaction = self.get_object()

        # Ensure the borrower can only return their own borrowed books
        if transaction.borrower != self.request.user.borrower:
            raise PermissionDenied("You can only return books you have borrowed.")

        # Ensure the book has not already been returned
        if transaction.is_returned:
            return Response({"error": "This book has already been returned."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the transaction as returned and update the book's status
        transaction.is_returned = True
        transaction.returned_date = timezone.now()
        transaction.save()

        # Free the book for other borrowers
        transaction.book.borrowed_by = None
        transaction.book.save()

        return Response({"message": "Book returned successfully!"}, status=status.HTTP_200_OK)


# Reservation ViewSet
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restrict reservations to the ones made by the logged-in borrower."""
        return self.queryset.filter(borrower=self.request.user.borrower)

    @action(detail=True, methods=['post'])
    def reserve_book(self, request, pk=None):
        """Allow a borrower to reserve a book if it is already borrowed but not reserved"""
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the book is currently borrowed
        if not book.borrowed_by:
            return Response({"error": "Book is not currently borrowed, cannot be reserved."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the book is already reserved by someone else
        if book.reserved_by:
            return Response({"error": "Book is already reserved by someone else."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the current borrowing transaction
        borrowing_transaction = BorrowingTransaction.objects.filter(book=book, is_returned=False).first()

        if not borrowing_transaction:
            return Response({"error": "No valid borrowing transaction found."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the expiration date for the reservation (10 days after the book's due date)
        expiration_date = borrowing_transaction.due_date + timezone.timedelta(days=10)

        # Create the reservation
        reservation = Reservation.objects.create(
            borrower=request.user.borrower,
            book=book,
            expiration_date=expiration_date
        )

        # Update the book to reflect that it's reserved
        book.reserved_by = request.user.borrower
        book.save()

        return Response({"message": "Book reserved successfully!", "expiration_date": expiration_date}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        """Allow the borrower to cancel their own reservation."""
        try:
            reservation = self.get_object()  # Get the reservation by primary key
        except Reservation.DoesNotExist:
            return Response({"error": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

        borrower = request.user.borrower

        # Check if the borrower owns the reservation
        if reservation.borrower != borrower:
            return Response({"error": "You do not have permission to cancel this reservation."}, status=status.HTTP_403_FORBIDDEN)

        # Clear the reservation from the Book and delete the reservation record
        book = reservation.book
        book.reserved_by = None
        book.save()

        reservation.delete()

        return Response({"message": "Your reservation has been canceled."}, status=status.HTTP_200_OK)


# Review ViewSet
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Allow users to see all reviews for any book."""
        return self.queryset

    def perform_create(self, serializer):
        """Allow users to create a review for books they've borrowed and update the book's average rating."""
        borrower = self.request.user.borrower
        book = serializer.validated_data['book']

        # Check if the borrower has borrowed the book before
        if not BorrowingTransaction.objects.filter(borrower=borrower, book=book).exists():
            raise ValidationError("You can only review books that you have borrowed.")

        # Save the review
        serializer.save(borrower=borrower)

        # Update the book's average rating
        self.update_book_average_rating(book)

    def perform_update(self, serializer):
        """Allow users to update their own reviews and update the book's average rating."""
        review = self.get_object()
        serializer.save()

        # Update the book's average rating after the review is updated
        self.update_book_average_rating(review.book)

    def perform_destroy(self, instance):
        """Allow users to delete their reviews and update the book's average rating."""
        book = instance.book
        instance.delete()

        # Update the book's average rating after the review is deleted
        self.update_book_average_rating(book)

    def update_book_average_rating(self, book):
        """Calculate and update the average rating of a book based on all its reviews."""
        average_rating = Review.objects.filter(book=book).aggregate(Avg('rating'))['rating__avg'] or 0
        book.average_rating = average_rating
        book.save()

    @action(detail=False, methods=['get'], url_path='book/(?P<book_id>[^/.]+)')
    def reviews_by_book(self, request, book_id=None):
        """Get all reviews for a specific book."""
        reviews = self.queryset.filter(book__id=book_id)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return notifications for the logged-in user only.
        """
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a notification as read.
        """
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({"message": "Notification marked as read"})
