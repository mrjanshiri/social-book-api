from django.db import models
from django.contrib.auth.models import AbstractUser

class Account(AbstractUser):
    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),  # نقش اصلی
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    email = models.EmailField(unique=True, blank=False, null=False) 
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.username 
