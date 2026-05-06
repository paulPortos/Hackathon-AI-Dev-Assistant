from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from users.urls import auth_urlpatterns
from scrum.views.calendar_views import CalendarRangeView, EventViewSet
from rest_framework.routers import DefaultRouter

calendar_router = DefaultRouter()
calendar_router.register(r'events', EventViewSet, basename='calendar-event')


api_urlpatterns = [
    path('agents/', include(('multi_agent.urls', 'multi_agent'), namespace='agents')),
    path('auth/tokens/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('auth/tokens/verify/', TokenVerifyView.as_view(), name='auth-token-verify'),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('scrum/', include(('scrum.urls', 'scrum'), namespace='scrum')),
    path('calendar/', CalendarRangeView.as_view(), name='calendar'),
    path('calendar/', include(calendar_router.urls)),
    path('', include(('scrum.urls', 'scrum_kanban'), namespace='kanban')),
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('user-descriptions/', include(('user_descriptions.urls', 'user_descriptions'), namespace='user-descriptions')),
]

urlpatterns = [
    path('auth/', include((auth_urlpatterns, 'auth'), namespace='auth')),
    path('api/<str:version>/', include((api_urlpatterns, 'api'), namespace='api')),
]
