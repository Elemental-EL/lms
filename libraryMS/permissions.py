from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthor(BasePermission):
    def has_permission(self, request, view):
        # Ensure that the user is authenticated and is an Author
        return request.user and request.user.is_authenticated and hasattr(request.user, 'author')

    def has_object_permission(self, request, view, obj):
        # Ensure that authors can only manage their own books
        return obj.author == request.user.author


# Each user can edit their own information
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user  # Only the user can edit their own information
