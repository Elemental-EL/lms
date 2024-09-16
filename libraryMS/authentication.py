from django.contrib.auth.backends import ModelBackend
from .models import Author, Borrower


class CustomModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Check Author model
            user = Author.objects.get(username=username)
            if user.check_password(password):
                return user
        except Author.DoesNotExist:
            pass

        try:
            # Check Borrower model
            user = Borrower.objects.get(username=username)
            if user.check_password(password):
                return user
        except Borrower.DoesNotExist:
            pass

        return None
