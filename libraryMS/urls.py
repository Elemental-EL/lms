from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path
from rest_framework.routers import DefaultRouter
from libraryMS.views import SignUpView, AuthorViewSet, BorrowerViewSet, BookViewSet, BorrowingTransactionViewSet, ReservationViewSet, ReviewViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'borrowers', BorrowerViewSet, basename='borrower')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrowings', BorrowingTransactionViewSet, basename='borrowing')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += router.urls
