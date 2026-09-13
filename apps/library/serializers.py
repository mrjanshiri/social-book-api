from rest_framework import serializers
from apps.catalog.models import Book
from .models import Shelf


class ShelfBookMiniSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    publisher = serializers.StringRelatedField(read_only=True)
    categories = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ['id','title', 'author', 'publisher', 'categories', 'description']


class ShelfSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    book = ShelfBookMiniSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        write_only=True
    )

    class Meta:
        model = Shelf
        fields = ['user', 'book', 'book_id', 'note', 'status', 'added_at', 'finished_at', 'is_private']
        read_only_fields = ['added_at', 'finished_at']

    def validate(self, attrs):
        if self.instance is None:
            request = self.context.get('request')
            book = attrs.get('book')
            if request and book and Shelf.objects.filter(user=request.user, book=book).exists():
                raise serializers.ValidationError({"book_id": "This book is already on your shelf."})
        return attrs

    def update(self, instance, validated_data):
        if 'book' in validated_data:
            raise serializers.ValidationError({"book_id": "book_id cannot be changed after creation."})
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or instance.user != request.user:
            data.pop('note', None)
        return data