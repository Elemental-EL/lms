from celery import shared_task
from libraryMS.models import Notification
from django.contrib.auth.models import User
from django.utils import timezone
from .models import BorrowingTransaction, Reservation


@shared_task
def send_in_app_notification(user_id, message):
    pass


@shared_task
def cancel_expired_reservations():
    """Cancel reservations where the expiration date has passed."""
    now = timezone.now()
    expired_reservations = Reservation.objects.filter(expiration_date__lt=now)

    for reservation in expired_reservations:
        Notification.objects.create(
            user=reservation.borrower,
            message=f"Attention: Your reservation for {reservation.book.title} has expired."
        )
        reservation.delete()


@shared_task
def send_reservation_available_notifications():
    """Create in-app notifications for borrowers when a reserved book becomes available."""
    available_reservations = Reservation.objects.filter(book__borrowed_by=None, expiration_date__gt=timezone.now())

    for reservation in available_reservations:
        borrower = reservation.borrower
        book = reservation.book
        # Create an in-app notification for the borrower
        Notification.objects.create(
            user=borrower,
            message=f"Good news! The book '{book.title}' you reserved is now available. Please borrow it before {reservation.expiration_date}."
        )


@shared_task
def send_due_date_notifications():
    """Create in-app notifications for borrowers when the book's due date is approaching."""
    now = timezone.now()
    reminder_date = now + timezone.timedelta(days=3)  # Notify 3 days before the due date
    approaching_due_books = BorrowingTransaction.objects.filter(due_date__lte=reminder_date, is_returned=False)

    for transaction in approaching_due_books:
        borrower = transaction.borrower
        book = transaction.book
        # Create an in-app notification for the borrower
        Notification.objects.create(
            user=borrower,
            message=f"Reminder: Your borrowed book '{book.title}' is due on {transaction.due_date}."
        )


@shared_task
def send_overdue_notifications():
    """Create in-app notifications for borrowers when the book's overdue."""
    reminder_date = timezone.now()
    overdue_books = BorrowingTransaction.objects.filter(due_date__lte=reminder_date, is_returned=False)

    for transaction in overdue_books:
        borrower = transaction.borrower
        book = transaction.book
        # Create an in-app notification for the borrower
        Notification.objects.create(
            user=borrower,
            message=f"Attention: Your borrowed book '{book.title}' is overdue, please return it."
        )
