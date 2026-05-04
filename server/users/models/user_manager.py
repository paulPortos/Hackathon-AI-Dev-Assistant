from django.contrib.auth.base_user import BaseUserManager


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
