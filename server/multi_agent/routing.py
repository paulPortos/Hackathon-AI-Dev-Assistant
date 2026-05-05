from django.urls import path

from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer
from multi_agent.consumers.ws_health_consumer import WsHealthConsumer

websocket_urlpatterns = [
    path('ws/health/', WsHealthConsumer.as_asgi()),
    path('ws/sr-dev/sessions/<int:session_id>/', SeniorDevSessionConsumer.as_asgi()),
]
