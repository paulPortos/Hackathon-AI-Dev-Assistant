from django.urls import path, re_path
from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer
from scrum.consumers import ScrumLiveConsumer

websocket_urlpatterns = [
    re_path(r'^ws/sr-dev/sessions/(?P<session_id>\d+)/$', SeniorDevSessionConsumer.as_asgi()),
    path('ws/scrum-live/', ScrumLiveConsumer.as_asgi()),
]
