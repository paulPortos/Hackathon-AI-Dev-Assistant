from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from users.urls import auth_urlpatterns


api_urlpatterns = [
    path('agents/', include(('multi_agent.urls', 'multi_agent'), namespace='agents')),
    path('auth/tokens/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('auth/tokens/verify/', TokenVerifyView.as_view(), name='auth-token-verify'),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('scrum/', include(('scrum.urls', 'scrum'), namespace='scrum')),
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('user-descriptions/', include(('user_descriptions.urls', 'user_descriptions'), namespace='user-descriptions')),
]

urlpatterns = [
    path('auth/', include((auth_urlpatterns, 'auth'), namespace='auth')),
    path('api/<str:version>/', include((api_urlpatterns, 'api'), namespace='api')),
]
