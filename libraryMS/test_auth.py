import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from libraryMS.models import Author, Borrower


@pytest.mark.django_db
class TestAuthentication:

    def setup_method(self):
        self.client = APIClient()

    def test_signup_author(self):
        url = reverse('signup')
        data = {
            "user_type": "author",
            "username": "author1",
            "password": "testpass123",
            "email": "author1@test.com",
            "name": "Author Name",
            "biography": "This is a biography.",
            "nationality": "Authorland",
            "date_of_birth": "1990-01-01"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Author.objects.filter(username='author1').exists()

    def test_signup_borrower(self):
        url = reverse('signup')
        data = {
            "user_type": "borrower",
            "username": "borrower1",
            "password": "testpass123",
            "email": "borrower1@test.com",
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Borrower.objects.filter(username='borrower1').exists()

    def test_login_author(self):
        author = Author.objects.create_user(
            username="author1", email="author1@test.com", password="testpass123", date_of_birth="1990-01-01"
        )
        url = reverse('token_obtain_pair')
        data = {
            "username": "author1",
            "password": "testpass123"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_token_refresh_author(self):
        author = Author.objects.create_user(
            username="author1", email="author1@test.com", password="testpass123", date_of_birth="1990-01-01"
        )
        login_url = reverse('token_obtain_pair')
        refresh_url = reverse('token_refresh')

        # First obtain the tokens
        login_response = self.client.post(login_url, {
            "username": "author1",
            "password": "testpass123"
        })
        refresh_token = login_response.data['refresh']

        # Now refresh the token
        refresh_response = self.client.post(refresh_url, {"refresh": refresh_token})
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data

    def test_login_borrower(self):
        borrower = Borrower.objects.create_user(
            username="borrower1", email="borrower1@test.com", password="testpass123"
        )
        url = reverse('token_obtain_pair')
        data = {
            "username": "borrower1",
            "password": "testpass123"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_token_refresh_borrower(self):
        borrower = Borrower.objects.create_user(
            username="borrower1", email="borrower1@test.com", password="testpass123"
        )
        login_url = reverse('token_obtain_pair')
        refresh_url = reverse('token_refresh')

        # First obtain the tokens
        login_response = self.client.post(login_url, {
            "username": "borrower1",
            "password": "testpass123"
        })
        refresh_token = login_response.data['refresh']

        # Now refresh the token
        refresh_response = self.client.post(refresh_url, {"refresh": refresh_token})
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data
