from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet , AuthorViewSet , PublisherViewSet , CategoryViewSet

router = DefaultRouter()

router.register(r'books', BookViewSet)
router.register(r'authors', AuthorViewSet)         
router.register(r'publishers', PublisherViewSet)   
router.register(r'categories', CategoryViewSet)  




urlpatterns = [
    path('', include(router.urls)),
]


