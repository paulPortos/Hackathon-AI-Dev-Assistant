from django.urls import path

from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer
from multi_agent.consumers.ws_health_consumer import WsHealthConsumer
from django.urls import path, re_path
from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer
from scrum.consumers import ScrumLiveConsumer, KanbanConsumer

websocket_urlpatterns = [
    path('ws/health/', WsHealthConsumer.as_asgi()),
    path('ws/sr-dev/sessions/<int:session_id>/', SeniorDevSessionConsumer.as_asgi()),
    re_path(r'^ws/sr-dev/sessions/(?P<session_id>\d+)/$', SeniorDevSessionConsumer.as_asgi()),
    re_path(r'^ws/scrum-live/(?P<project_id>\d+)/(?:(?P<session_id>\d+)/)?$', ScrumLiveConsumer.as_asgi()),
    re_path(r'^ws/kanban/(?P<board_id>\d+)/$', KanbanConsumer.as_asgi()),
]
