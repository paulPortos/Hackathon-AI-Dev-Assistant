from django.urls import path, re_path
from multi_agent.consumers.senior_dev_session_consumer import SeniorDevSessionConsumer
from scrum.consumers import ScrumLiveConsumer, KanbanConsumer

websocket_urlpatterns = [
    re_path(r'^ws/sr-dev/sessions/(?P<session_id>\d+)/$', SeniorDevSessionConsumer.as_asgi()),
    re_path(r'^ws/scrum-live/(?P<project_id>\d+)/(?:(?P<session_id>\d+)/)?$', ScrumLiveConsumer.as_asgi()),
    re_path(r'^ws/kanban/(?P<board_id>\d+)/$', KanbanConsumer.as_asgi()),
]
