from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path
from rest_framework.routers import DefaultRouter
from libraryMS.views import AuthorViewSet, BorrowerViewSet, BookViewSet, BorrowingTransactionViewSet, ReservationViewSet, ReviewViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'borrowers', BorrowerViewSet)
router.register(r'books', BookViewSet)
router.register(r'borrowings', BorrowingTransactionViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += router.urls
