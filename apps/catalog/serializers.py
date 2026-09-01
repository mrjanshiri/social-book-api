from rest_framework import serializers
from .models import Author, Publisher, Category, Book
from .utils import normalize_isbn
from apps.reviews.serializers import ReviewSerializer


class AuthorSerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'birth_date', 'books']

class PublisherSerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'address', 'books']

class CategorySerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'books']


class BookSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    publisher = serializers.StringRelatedField(read_only=True)
    categories = serializers.StringRelatedField(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True) 

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        source='author',
        write_only=True
    )

    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        source='publisher',
        write_only=True,
        required=False,
        allow_null=True,
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source='categories',
        write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'publisher', 'categories', 'publication_date',
            'isbn', 'pages', 'description', 'average_rating', 'reviews',
            'author_id', 'publisher_id', 'category_ids' , 'added_by'
        ]
        read_only_fields = ['average_rating', 'author', 'publisher', 'categories', 'reviews']

    def validate_isbn(self, value):
        try:
            return normalize_isbn(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def create(self, validated_data):
        author_obj = validated_data.pop('author') 
        publisher_obj = validated_data.pop('publisher', None) 
        category_objs = validated_data.pop('categories', []) 

        book = Book.objects.create(author=author_obj, publisher=publisher_obj, **validated_data)

        book.categories.set(category_objs)

        return book

    def update(self, instance, validated_data):

        categories_provided = 'categories' in validated_data
        publisher_provided = 'publisher' in validated_data

        author_obj = validated_data.pop('author', None)
        publisher_obj = validated_data.pop('publisher', None)
        category_objs = validated_data.pop('categories', None)

        if author_obj:
            instance.author = author_obj
        if publisher_provided:
            instance.publisher = publisher_obj

        if categories_provided:
            instance.categories.set(category_objs)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance