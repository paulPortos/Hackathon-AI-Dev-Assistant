from django.urls import re_path
from .consumers import ScrumLiveConsumer

websocket_urlpatterns = [
    re_path(r'^ws/scrum-live/$', ScrumLiveConsumer.as_asgi()),
]
