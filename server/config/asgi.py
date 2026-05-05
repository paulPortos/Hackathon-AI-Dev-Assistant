"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from config.middleware.jwt_auth_middleware import JwtAuthMiddlewareStack
from multi_agent.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        'http': django_asgi_app,
        'websocket': JwtAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns),
        ),
    }
)
