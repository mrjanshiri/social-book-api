"""
Keeps Book.average_rating in sync with its reviews.

Why a signal and not a save()/delete() override on Review: deleting a user
(or a book, or using queryset.delete()) removes reviews without ever calling
Review.delete(), so the override would leave stale averages. Signals fire in
all of those paths.

The calculation itself lives in catalog (Book.update_average_rating); this
module only decides *when* to call it.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


@receiver((post_save, post_delete), sender=Review)
def refresh_book_rating(sender, instance, **kwargs):
    instance.book.update_average_rating()