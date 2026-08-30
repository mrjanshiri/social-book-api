from django.shortcuts import render
from rest_framework import viewsets , status , permissions
from rest_framework.decorators import action 
from rest_framework.response import Response
from apps.core.permissions import IsAdminOrSelfReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg
from rest_framework.permissions import IsAuthenticated
from .filters import BookFilter
import django_filters
from .models import Book, Author, Publisher, Category
from .serializers import BookSerializer, AuthorSerializer, PublisherSerializer, CategorySerializer
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer, ReviewCreateSerializer


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSelfReadOnly]
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = BookFilter



    @action(detail=True, methods=['get', 'post'], url_path='reviews' , permission_classes=[permissions.AllowAny])
    def reviews(self, request, pk=None):
        book = self.get_object()

        if request.method == 'GET':

            reviews_qs = Review.objects.filter(book=book)
            serializer = ReviewSerializer(reviews_qs, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            print('enterd')
            if not request.user.is_authenticated:
                return Response({"detail": "Authentication credentials were not provided."}, status=401)
            if Review.objects.filter(book = book , user = request.user).exists():
                return Response(
                {"detail": "you already created a reviews"},
                status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ReviewCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(book=book, user=request.user)
                return Response(ReviewSerializer(serializer.instance).data, status=201)
            return Response(serializer.errors, status=400)
        

    @action(detail=False, methods=['get'], url_path='most-reviewed')
    def most_reviewed(self, request):
        books = Book.objects.annotate(
            num_reviews=Count('reviews')
        ).order_by('-num_reviews')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    

    @action(detail=False, methods=['get'], url_path='most-wishlisted')
    def most_wishlisted(self, request):
        books = Book.objects.annotate(
            num_wishlisted=Count('wishlistitems')
        ).order_by('-num_wishlisted')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    

    @action(detail=False, methods=['get'], url_path='top-rated')
    def top_rated(self , request):
        books = Book.objects.all().order_by('-average_rating')
        serializer = self.get_serializer(books , many = True)
        return Response(serializer.data)


    

class AuthorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSelfReadOnly]

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    @action(detail=True, methods=['get'], url_path='books') 
    def list_books(self, request, pk=None):
        try:
            author = self.get_object()
            books = Book.objects.filter(author = author)
            serializer = BookSerializer(books , many = True)
            return Response(serializer.data)
        except Author.DoesNotExist:
            return Response({"detail": "author doesnt found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PublisherViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSelfReadOnly]
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer


    @action(detail=True , methods=['get'] , url_path='books')
    def list_book(self , request , pk = None):
        try:
            publisher = self.get_object()
            print(publisher)
            print(type(publisher))
            books = Book.objects.filter(publisher = publisher)
            serializer = BookSerializer(books , many = True)
            return Response(serializer.data)
        except Publisher.DoesNotExist:
            return Response({"detail": "publisher doesnt found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrSelfReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @action(detail=True, methods=['get'], url_path='books')
    def list_books(self, request, pk=None):
        try:
            category = self.get_object()
            books = Book.objects.filter(categories=category) 
            serializer = BookSerializer(books, many=True)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({"detail": "Categories doesnt found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    

    


