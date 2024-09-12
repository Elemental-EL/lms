from django.shortcuts import render

# Create your views here.

from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
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

        # Check if the book is already borrowed or reserved
        if book.borrowed_by or book.reserved_by:
            raise PermissionDenied("This book is currently borrowed or reserved by someone else.")

        # Check if the borrower already has 5 borrowed books
        active_borrowings_count = BorrowingTransaction.objects.filter(borrower=borrower, is_returned=False).count()
        if active_borrowings_count >= 5:
            raise PermissionDenied("You cannot borrow more than 5 books at a time.")

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
    permission_classes = [CanReserveBook | IsBorrower]


# Review ViewSet
class ReviewViewSet(viewsets.ModelViewSet):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # If the user is an author, return reviews for their own books
        if hasattr(user, 'author'):
            author_books = Book.objects.filter(author=user.author)
            return Review.objects.filter(book__in=author_books)


        return Review.objects.none()


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
