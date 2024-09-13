from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser


class Author(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='author_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='author_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    name = models.CharField(max_length=255)
    biography = models.TextField()
    nationality = models.CharField(max_length=100)
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name


class Borrower(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='borrower_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='borrower_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class Book(models.Model):
    CATEGORY_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-fiction'),
        ('fantasy', 'Fantasy'),
        ('mystery', 'Mystery'),
        ('biography', 'Biography'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    ISBN = models.CharField(max_length=13, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=False, null=False)
    publication_date = models.DateField()
    average_rating = models.FloatField(default=0)
    borrowed_by = models.OneToOneField(Borrower, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='borrowed_book')
    reserved_by = models.OneToOneField(Borrower, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='reserved_book')

    def __str__(self):
        return self.title


class BorrowingTransaction(models.Model):
    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.borrower.username} borrowed {self.book.title}"


class Reservation(models.Model):
    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    expiration_date = models.DateTimeField()

    def __str__(self):
        return f"{self.borrower.username} reserved {self.book.title}"


class Review(models.Model):
    borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    review_message = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f"Review by {self.borrower.username} for {self.book.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}"
