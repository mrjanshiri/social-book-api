from django.db import models
from apps.catalog.models import Book
from apps.users.models import Account


class WishlistItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='wishlist_items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlistitems')
    note = models.CharField(max_length=225, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.book.title} for {self.user.username}"