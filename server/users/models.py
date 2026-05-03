from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, github_id, username, password=None, **extra_fields):
        if not github_id:
            raise ValueError('The github_id field is required')
        if not username:
            raise ValueError('The username field is required')

        user = self.model(github_id=str(github_id), username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, github_id, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        if not password:
            raise ValueError('Superuser must have a password')

        return self.create_user(github_id, username, password, **extra_fields)


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
