from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import IsAdminOrReadOnly
from .permissions import IsBookOwnerOrAdminOrReadOnly
from django.db.models import Count, ProtectedError
from .filters import BookFilter
import django_filters
from .models import Book, Author, Publisher, Category
from .serializers import BookSerializer, AuthorSerializer, PublisherSerializer, CategorySerializer


BOOK_QUERYSET = Book.objects.select_related('author', 'publisher').prefetch_related(
    'categories', 'reviews__user'
)


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBookOwnerOrAdminOrReadOnly]
    queryset = BOOK_QUERYSET
    serializer_class = BookSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = BookFilter

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='most-reviewed')
    def most_reviewed(self, request):
        books = BOOK_QUERYSET.annotate(
            num_reviews=Count('reviews')
        ).order_by('-num_reviews')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='most-wishlisted')
    def most_wishlisted(self, request):
        books = BOOK_QUERYSET.annotate(
            num_wishlisted=Count('shelf_items')
        ).order_by('-num_wishlisted')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='top-rated')
    def top_rated(self, request):
        books = BOOK_QUERYSET.order_by('-average_rating')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This book cannot be deleted because it is on at least one user's shelf."},
                status=status.HTTP_409_CONFLICT
            )


class AuthorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Author.objects.prefetch_related('books')
    serializer_class = AuthorSerializer

    @action(detail=True, methods=['get'], url_path='books')
    def list_books(self, request, pk=None):
        author = self.get_object()
        books = BOOK_QUERYSET.filter(author=author)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class PublisherViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Publisher.objects.prefetch_related('books')
    serializer_class = PublisherSerializer

    @action(detail=True, methods=['get'], url_path='books')
    def list_books(self, request, pk=None):
        publisher = self.get_object()
        books = BOOK_QUERYSET.filter(publisher=publisher)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Category.objects.prefetch_related('books')
    serializer_class = CategorySerializer

    @action(detail=True, methods=['get'], url_path='books')
    def list_books(self, request, pk=None):
        category = self.get_object()
        books = BOOK_QUERYSET.filter(categories=category)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)