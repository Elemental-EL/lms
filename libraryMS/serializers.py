

from rest_framework import serializers
from libraryMS.models import Author, Borrower, Book, BorrowingTransaction, Reservation, Review, Notification


# Sign up Serializer
class SignUpSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=[('author', 'Author'), ('borrower', 'Borrower')])
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()

    # Additional fields for author
    name = serializers.CharField(required=False, allow_blank=True)
    biography = serializers.CharField(required=False, allow_blank=True)
    nationality = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    # Additional fields for borrower
    registration_date = serializers.DateField(required=False, allow_null=True)

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        # Depending on the user type, create additional information
        if user_type == 'author':
            user = Author(
                username=validated_data['username'],
                email=validated_data['email'],
                name=validated_data['name'],
                biography=validated_data['biography'],
                nationality=validated_data['nationality'],
                date_of_birth=validated_data['date_of_birth'],
            )
            user.set_password(validated_data['password'])
            user.save()
            return user
        elif user_type == 'borrower':
            user = Borrower(
                username=validated_data['username'],
                email=validated_data['email'],
            )
            user.set_password(validated_data['password'])
            user.save()
            return user


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

    def update(self, instance, validated_data):
        # Allow updating fields other than borrowed_by, reserved_by, and average_rating
        for attr, value in validated_data.items():
            if attr not in ['borrowed_by', 'reserved_by', 'average_rating']:
                setattr(instance, attr, value)
        instance.save()
        return instance


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
