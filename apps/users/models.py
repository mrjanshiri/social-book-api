from django.contrib.auth.models import AbstractUser
from django.db import models, transaction


class Account(AbstractUser):

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False
    )

    first_name = models.CharField(
        max_length=100,
        blank=True
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'profile_picture' not in update_fields:
            return super().save(*args, **kwargs)

        old_name = None
        if self.pk:
            old_name = (
                type(self).objects.filter(pk=self.pk)
                .values_list('profile_picture', flat=True)
                .first()
            )
        super().save(*args, **kwargs)
        if old_name and old_name != self.profile_picture.name:
            self._delete_file_after_commit(self.profile_picture.storage, old_name)

    def delete(self, *args, **kwargs):
        name = self.profile_picture.name
        storage = self.profile_picture.storage
        result = super().delete(*args, **kwargs)
        if name:
            self._delete_file_after_commit(storage, name)
        return result

    @staticmethod
    def _delete_file_after_commit(storage, name):
        transaction.on_commit(lambda: storage.delete(name))