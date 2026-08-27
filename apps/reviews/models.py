from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.catalog.models import Book
from apps.users.models import Account


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')

    def __str__(self):
        return f'Review for {self.book.title} by {self.user}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.book.update_average_rating()

    def delete(self, *args, **kwargs):
        book = self.book
        super().delete(*args, **kwargs)
        book.update_average_rating()