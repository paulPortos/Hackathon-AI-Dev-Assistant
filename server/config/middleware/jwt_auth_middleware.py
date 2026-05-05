from urllib.parse import parse_qs

import logging

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()
        self.logger = logging.getLogger('api.errors')

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = self._get_token(scope)
        if token:
            user, error = await self._get_user(token)
            scope['user'] = user
            if error:
                scope['jwt_error'] = error
                self.logger.warning('WebSocket JWT auth failed: %s', error)
        return await self.inner(scope, receive, send)

    def _get_token(self, scope):
        query_string = scope.get('query_string', b'')
        if not query_string:
            return ''
        params = parse_qs(query_string.decode('utf-8'))
        tokens = params.get('token') or params.get('access_token') or []
        if not tokens:
            return ''
        token = tokens[0].strip()
        if token.lower().startswith('bearer '):
            token = token[7:].strip()
        return token

    @sync_to_async
    def _get_user(self, token):
        try:
            validated = self.jwt_auth.get_validated_token(token)
            return self.jwt_auth.get_user(validated), ''
        except Exception as exc:
            return AnonymousUser(), str(exc)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)
