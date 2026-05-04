from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from users.views import EmailVerificationConfirmView, EmailVerificationRequestView
from users.views import GitHubCallbackView, GitHubLoginView, MeView


api_v1_urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('email-verifications/request/', EmailVerificationRequestView.as_view(), name='email-verification-request'),
    path('email-verifications/confirm/', EmailVerificationConfirmView.as_view(), name='email-verification-confirm'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
]

auth_urlpatterns = [
    path('github/login/', GitHubLoginView.as_view(), name='github-login'),
    path('github/callback/', GitHubCallbackView.as_view(), name='github-callback'),
]

urlpatterns = [
    path('api/<str:version>/', include((api_v1_urlpatterns, 'users'), namespace='users-api')),
]
