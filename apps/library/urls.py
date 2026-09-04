from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShelfViewSet

router = DefaultRouter()
router.register(r'shelf', ShelfViewSet, basename='shelf')

urlpatterns = [
    path('', include(router.urls)),
]