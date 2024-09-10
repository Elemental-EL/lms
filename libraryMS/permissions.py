from rest_framework.permissions import BasePermission, SAFE_METHODS


# Admins have full access to all resources
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# Only authors can create books and can edit or delete their own books
class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Authors can create books
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.is_author
        return True

    def has_object_permission(self, request, view, obj):
        # Authors can edit or delete their own books
        if request.method in SAFE_METHODS:
            return True  # Read-only permissions for everyone
        return obj.author == request.user  # Only the author can modify the book


# Each user can edit their own information
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user  # Only the user can edit their own information


# Borrowers can't borrow a book if it's already borrowed or reserved by someone else
class CanBorrowBook(BasePermission):
    def has_permission(self, request, view):
        book = view.get_object()
        if request.method == 'POST':
            return not book.borrowed_by and not book.reserved_by  # Can't borrow if already borrowed or reserved
        return True


# Reservations can only be made if the book is borrowed and not reserved
class CanReserveBook(BasePermission):
    def has_permission(self, request, view):
        book = view.get_object()
        if request.method == 'POST':
            return book.borrowed_by and not book.reserved_by  # Can only reserve if borrowed and not reserved
        return True


# Borrowers can only make one review per book
class CanReviewBook(BasePermission):
    def has_permission(self, request, view):
        book = view.get_object()
        borrower = request.user

        # Check if the borrower has already reviewed this book
        if request.method == 'POST':
            return not book.review_set.filter(borrower=borrower).exists()
        return True


# Pretty self-explanatory
class IsBorrower(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.borrower == request.user
