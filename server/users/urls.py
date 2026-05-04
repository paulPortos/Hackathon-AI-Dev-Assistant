from django.urls import path

from users.views import GitHubCallbackView, GitHubLoginView, MeView, UserPublicDetailView


app_name = 'users'

urlpatterns = [
    path(
        'me/',
        MeView.as_view(),
        name='current-user-detail'
    ),
    path(
        '<int:user_id>/',
        UserPublicDetailView.as_view(),
        name='user-detail'
    ),
]

auth_urlpatterns = [
    path(
        'github/login/',
        GitHubLoginView.as_view(),
        name='github-oauth-login'
    ),
    path(
        'github/callback/',
        GitHubCallbackView.as_view(),
        name='github-oauth-callback'
    ),
]
