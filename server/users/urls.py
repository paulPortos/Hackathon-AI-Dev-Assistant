from django.urls import path

from users.views import EmailVerificationConfirmView, EmailVerificationRequestView
from users.views import GitHubCallbackView, GitHubLoginView, MeView


app_name = 'users'

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
]

auth_urlpatterns = [
    path('github/login/', GitHubLoginView.as_view(), name='github-login'),
    path('github/callback/', GitHubCallbackView.as_view(), name='github-callback'),
]

email_verification_urlpatterns = [
    path('request/', EmailVerificationRequestView.as_view(), name='email-verification-request'),
    path('confirm/', EmailVerificationConfirmView.as_view(), name='email-verification-confirm'),
]
