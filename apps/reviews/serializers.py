from rest_framework import serializers
from apps.catalog.models import Book
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    book = serializers.StringRelatedField(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
    )

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_id', 'book', 'book_id', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        # Friendly 400 before hitting the DB constraint. The constraint plus
        # the IntegrityError handler in the view covers the concurrent case.
        if self.instance is None:
            request = self.context['request']
            if Review.objects.filter(user=request.user, book=attrs['book']).exists():
                raise serializers.ValidationError(
                    {'book_id': 'You have already reviewed this book.'}
                )
        return attrs

    def update(self, instance, validated_data):
        book = validated_data.pop('book', None)
        if book is not None and book.pk != instance.book_id:
            raise serializers.ValidationError(
                {'book_id': 'book_id cannot be changed after creation.'}
            )
        return super().update(instance, validated_data)


class ReviewCreateSerializer(serializers.ModelSerializer):
    # TODO: remove in step 3, only the old catalog action still uses it.
    class Meta:
        model = Review
        fields = ['rating', 'comment']