from django.db import models
from apps.catalog.models import Book
from apps.users.models import Account


class Shelf(models.Model):
    STATUS_TO_READ = 'to_read'
    STATUS_READING = 'reading'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = [
        (STATUS_TO_READ, 'To Read'),
        (STATUS_READING, 'Reading'),
        (STATUS_FINISHED, 'Finished'),
    ]

    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='shelf_items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='shelf_items')
    note = models.CharField(max_length=225, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_TO_READ)
    added_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.book.title} for {self.user.username}"

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_FINISHED and self.finished_at is None:
            from django.utils import timezone
            self.finished_at = timezone.now()
        elif self.status != self.STATUS_FINISHED:
            self.finished_at = None
        super().save(*args, **kwargs)