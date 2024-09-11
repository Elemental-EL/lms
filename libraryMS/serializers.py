from rest_framework import serializers
from libraryMS.models import Author, Borrower, Book, BorrowingTransaction, Reservation, Review, Notification


# Author Serializer
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'username', 'email', 'name', 'biography', 'nationality', 'date_of_birth']


# Borrower Serializer
class BorrowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrower
        fields = ['id', 'username', 'email', 'registration_date']


# Book Serializer
class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)  # Nested serializer for author details
    borrowed_by = BorrowerSerializer(read_only=True)  # Nested serializer for borrower details
    reserved_by = BorrowerSerializer(read_only=True)  # Nested serializer for reservation details

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'description', 'author', 'ISBN', 'category',
            'publication_date', 'average_rating', 'borrowed_by', 'reserved_by'
        ]


# Borrowing Transaction Serializer
class BorrowingTransactionSerializer(serializers.ModelSerializer):
    borrower = BorrowerSerializer(read_only=True)  # Nested serializer for borrower
    book = BookSerializer(read_only=True)  # Nested serializer for book details

    class Meta:
        model = BorrowingTransaction
        fields = ['id', 'borrower', 'book', 'borrowed_date', 'due_date', 'is_returned']


# Reservation Serializer
class ReservationSerializer(serializers.ModelSerializer):
    borrower = BorrowerSerializer(read_only=True)  # Nested serializer for borrower
    book = BookSerializer(read_only=True)  # Nested serializer for book

    class Meta:
        model = Reservation
        fields = ['id', 'borrower', 'book', 'expiration_date']


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    borrower = BorrowerSerializer(read_only=True)  # Nested serializer for borrower
    book = BookSerializer(read_only=True)  # Nested serializer for book details

    class Meta:
        model = Review
        fields = ['id', 'borrower', 'book', 'review_message', 'rating']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'read']
