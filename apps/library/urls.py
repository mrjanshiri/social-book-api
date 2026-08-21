from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WhishListItemViewSet

router = DefaultRouter()
router.register(r'whishlistitems', WhishListItemViewSet, basename='wishlistitem')

urlpatterns = [
    path('', include(router.urls)),
]