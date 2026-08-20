import django_filters
from .models import Book, Category # فرض می‌کنیم Category را هم import کردید

class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    # تغییر برای ManyToManyField
    categories = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(), # منبع دسته‌بندی‌ها
        field_name='categories__name', # فیلتر بر اساس نام دسته‌بندی در ManyToMany
        lookup_expr='icontains', # یا می توانید از 'exact' استفاده کنید اگر دقیقا می خواهید مچ شود
        # برای اینکه دقیقا مشابه مثال قبلی کار کند، می توانید از name استفاده کنید
        # field_name='categories',
        # lookup_expr='exact', # یا icontains
        # to_field_name='name' # اگر می خواهید مستقیما روی name فیلتر کنید
    )

    publisher = django_filters.CharFilter(field_name='publisher__name', lookup_expr='icontains') # این قسمت به شرطی درسته که Publisher هم name داشته باشه
    published_after = django_filters.DateFilter(lookup_expr='gte')
    published_before = django_filters.DateFilter(lookup_expr='lte')
    min_average_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_average_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')

    class Meta:
        model = Book
        # در fields، از 'categories' به جای 'category' استفاده کنید
        fields = ['title', 'categories', 'publisher', 'published_after', 'published_before', 'min_average_rating', 'max_average_rating']
