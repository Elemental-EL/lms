from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from libraryMS.models import Author, Borrower, Book, BorrowingTransaction, Reservation, Review, Notification
from libraryMS.serializers import (
    NotificationSerializer,
    AuthorSerializer,
    BorrowerSerializer,
    BookSerializer,
    BorrowingTransactionSerializer,
    ReservationSerializer,
    ReviewSerializer
)
from libraryMS.permissions import (
    IsAdmin,
    IsAuthorOrReadOnly,
    IsOwnerOrReadOnly,
    CanReserveBook,
    CanBorrowBook,
    CanReviewBook,
    IsBorrower
)
from rest_framework.decorators import action
from rest_framework.response import Response


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
    permission_classes = [IsAdmin | IsAuthorOrReadOnly]


# Borrowing Transaction ViewSet
class BorrowingTransactionViewSet(viewsets.ModelViewSet):
    queryset = BorrowingTransaction.objects.all()
    serializer_class = BorrowingTransactionSerializer
    permission_classes = [CanBorrowBook]


# Reservation ViewSet
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [CanReserveBook | IsBorrower]


# Review ViewSet
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [CanReviewBook | IsBorrower]

    def get_permissions(self):
        actionf = getattr(self, 'action', None)
        if actionf in ['update', 'partial_update', 'destroy']:
            return [IsBorrower()]
        return super().get_permissions()


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
