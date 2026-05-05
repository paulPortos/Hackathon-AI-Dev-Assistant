from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


class EncryptedTokenField(models.TextField):
    description = 'Encrypted token text'

    def _fernet(self):
        key = getattr(settings, 'GITHUB_TOKEN_ENCRYPTION_KEY', '')
        if not key:
            raise ImproperlyConfigured('GITHUB_TOKEN_ENCRYPTION_KEY is required')

        try:
            return Fernet(key.encode())
        except ValueError as exc:
            raise ImproperlyConfigured('GITHUB_TOKEN_ENCRYPTION_KEY must be a valid Fernet key') from exc

    def _looks_encrypted(self, value):
        return isinstance(value, str) and value.startswith('gAAAAA')

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value in (None, ''):
            return ''
        if not isinstance(value, str):
            return value

        try:
            return self._fernet().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            if self._looks_encrypted(value):
                raise ImproperlyConfigured('GITHUB_TOKEN_ENCRYPTION_KEY could not decrypt a stored GitHub token') from exc
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ''):
            return ''
        if not isinstance(value, str):
            value = str(value)

        if self._looks_encrypted(value):
            try:
                self._fernet().decrypt(value.encode())
                return value
            except InvalidToken as exc:
                raise ImproperlyConfigured('GITHUB_TOKEN_ENCRYPTION_KEY could not decrypt a stored GitHub token') from exc

        return self._fernet().encrypt(value.encode()).decode()
