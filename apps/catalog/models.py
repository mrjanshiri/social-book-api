from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import Account
class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    categories = models.ManyToManyField(Category, related_name='books')
    publication_date = models.DateField()
    isbn = models.CharField(max_length=13, unique=True, help_text='13-digit ISBN')
    pages = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    average_rating = models.FloatField(default=0.0) # به طور خودکار محاسبه می شود

    def __str__(self):
        return self.title

    def update_average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            self.average_rating = sum([r.rating for r in reviews]) / reviews.count()
        else:
            self.average_rating = 0.0
        self.save()


