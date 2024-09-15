import os

from celery import shared_task
from django.conf import settings
from django.db.models import Count, Q, F

from libraryMS.models import Notification, Book, Report
from django.contrib.auth.models import User
from django.utils import timezone
from .models import BorrowingTransaction, Reservation
from .utils import generate_pdf_report


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


@shared_task
def generate_report(report_id):
    try:
        report_instance = Report.objects.get(id=report_id)
        report_type = report_instance.report_type

        # Fetch the data based on report_type
        report_data = []

        if report_type == "most_borrowed_books":
            # Fetch the top 10 most borrowed books in the last month
            last_month = timezone.now() - timezone.timedelta(days=30)
            most_borrowed_books = (
                Book.objects.filter(borrowingtransaction__borrowed_date__gte=last_month)
                .annotate(borrow_count=Count('borrowingtransaction'))
                .order_by('-borrow_count')[:10]
            )
            report_data.append("Most Borrowed Books (Last Month):")
            for book in most_borrowed_books:
                report_data.append(f"{book.title} - Borrowed {book.borrow_count} times")

        elif report_type == "borrowers_with_overdue_books":
            # Fetch all borrowers who have overdue books
            overdue_borrowings = BorrowingTransaction.objects.filter(
                is_returned=False,
                due_date__lt=timezone.now()
            ).select_related('book', 'borrower')

            report_data.append("Borrowers with Overdue Books:")
            for borrowing in overdue_borrowings:
                overdue_days = (timezone.now() - borrowing.due_date).days
                report_data.append(
                    f"Borrower: {borrowing.borrower.username}, Book: {borrowing.book.title}, Overdue by {overdue_days} days"
                )

        elif report_type == "books_currently_checked_out":
            # Fetch all books currently checked out
            checked_out_books = BorrowingTransaction.objects.filter(
                is_returned=False
            ).select_related('book', 'borrower')

            report_data.append("Books Currently Checked Out:")
            for borrowing in checked_out_books:
                report_data.append(
                    f"Book: {borrowing.book.title}, Borrower: {borrowing.borrower.username}, Due Date: {borrowing.due_date}"
                )

        elif report_type == "books_in_high_demand":
            # Fetch books that have been frequently reserved or borrowed immediately after becoming available
            high_demand_books = (
                Book.objects.filter(
                    Q(borrowingtransaction__is_returned=True) | Q(reservation__isnull=False)
                )
                .annotate(
                    reservation_count=Count('reservation'),
                    borrow_count=Count('borrowingtransaction')
                )
                .filter(reservation_count__gt=0)  # Filtering to those with at least 1 reservation
                .order_by('-reservation_count', '-borrow_count')[:10]
            )
            report_data.append("Books in High Demand:")
            for book in high_demand_books:
                report_data.append(
                    f"{book.title} - Reserved {book.reservation_count} times, Borrowed {book.borrow_count} times"
                )

        elif report_type == "borrowing_trends":
            # Fetch borrowing trends (books borrowed per month)
            borrowing_trends = (
                BorrowingTransaction.objects
                .annotate(month=F('borrowed_date__month'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')
            )
            report_data.append("Borrowing Trends (Books Borrowed Per Month):")
            for trend in borrowing_trends:
                report_data.append(f"Month: {trend['month']} - {trend['count']} books borrowed")

        # Generate the PDF report and save it to the file system
        pdf_file_path = os.path.join(settings.MEDIA_ROOT, f'reports/report_{report_id}.pdf')
        generate_pdf_report(report_data, pdf_file_path)  # Save to file

        # Update the report instance
        report_instance.file = f'reports/report_{report_id}.pdf'
        report_instance.status = "completed"
        report_instance.save()

    except Exception as e:
        report_instance.status = "failed"
        report_instance.save()
        raise e