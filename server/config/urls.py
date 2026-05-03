from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from users.urls import auth_urlpatterns
from users.views import MeView


api_v1_patterns = [
    path('me/', MeView.as_view(), name='me'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include((auth_urlpatterns, 'auth'), namespace='auth')),
    path('api/me/', MeView.as_view(), name='api-me'),
    path('api/<str:version>/', include((api_v1_patterns, 'api'), namespace='api-v1')),
]
