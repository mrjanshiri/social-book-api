from django.db import models
from django.contrib.auth.models import AbstractUser


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