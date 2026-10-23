import django_filters

from .models import Review


class ReviewFilter(django_filters.FilterSet):
    book = django_filters.NumberFilter(field_name='book_id')
    user = django_filters.NumberFilter(field_name='user_id')

    class Meta:
        model = Review
        fields = ['rating']