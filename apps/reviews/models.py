from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Book
from apps.users.models import Account


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['book', 'user'],
                name='unique_review_per_user_and_book',
            ),
        ]

    def __str__(self):
        return f'Review for {self.book.title} by {self.user}'