from django.db import models
from apps.catalog.models import Book
from apps.users.models import Account


class Shelf(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='shelf_items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='shelf_items')
    note = models.CharField(max_length=225, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.book.title} for {self.user.username}"