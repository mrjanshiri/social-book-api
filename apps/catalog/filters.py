import django_filters
from .models import Book, Category

class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    categories = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        field_name='categories',
        lookup_expr='exact',
    )

    publisher = django_filters.CharFilter(field_name='publisher__name', lookup_expr='icontains') 
    published_after = django_filters.DateFilter(field_name='publication_date', lookup_expr='gte')
    published_before = django_filters.DateFilter(field_name='publication_date', lookup_expr='lte')
    min_average_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_average_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')

    class Meta:
        model = Book
        fields = ['title', 'categories', 'publisher']