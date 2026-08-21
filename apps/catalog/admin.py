from django.contrib import admin
from .models import Author, Publisher, Category, Book, WishlistItem
from apps.reviews.models import Review

# Register your models here.

admin.site.register(Author)
admin.site.register(Publisher)
admin.site.register(Category)
admin.site.register(Book)
admin.site.register(Review)
admin.site.register(WishlistItem)