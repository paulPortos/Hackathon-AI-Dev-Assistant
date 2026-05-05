from django.urls import re_path

from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer

websocket_urlpatterns = [
    re_path(r'^ws/sr-dev/sessions/(?P<session_id>\d+)/$', SeniorDevSessionConsumer.as_asgi()),
]
