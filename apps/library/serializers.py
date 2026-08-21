from rest_framework import serializers
from apps.catalog.models import Book
from .models import WishlistItem


class WishlistBookMiniSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    publisher = serializers.StringRelatedField(read_only=True)
    categories = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ['title', 'author', 'publisher', 'categories', 'description']


class WhisListItemSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = WishlistBookMiniSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ['user', 'book', 'book_id', 'note', 'added_at']
        read_only_fields = ['added_at']