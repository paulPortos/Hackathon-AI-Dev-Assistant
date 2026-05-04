from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from users.models.user_manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    github_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    avatar_url = models.URLField(blank=True)
    access_token = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'github_id'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username
