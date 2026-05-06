import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()

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
