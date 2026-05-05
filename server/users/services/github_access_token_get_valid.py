from django.db import transaction
from django.utils import timezone

from users.github import GitHubOAuthError, refresh_github_access_token
from users.services.github_token_error import GitHubTokenError
from users.services.github_token_update_from_data import github_token_update_from_data


@transaction.atomic
def github_access_token_get_valid(user):
    user = user.__class__.objects.select_for_update().get(id=user.id)
    if not user.access_token:
        raise GitHubTokenError('github_token_missing', 'GitHub account must be connected before reading repository code')

    refresh_threshold = timezone.now() + timezone.timedelta(minutes=2)
    if user.github_access_token_expires_at and user.github_access_token_expires_at <= refresh_threshold:
        if not user.github_refresh_token:
            raise GitHubTokenError('github_reconnect_required', 'GitHub token expired. Please reconnect GitHub')
        if user.github_refresh_token_expires_at and user.github_refresh_token_expires_at <= timezone.now():
            raise GitHubTokenError('github_reconnect_required', 'GitHub refresh token expired. Please reconnect GitHub')

        try:
            token_data = refresh_github_access_token(refresh_token=user.github_refresh_token)
        except GitHubOAuthError as exc:
            raise GitHubTokenError('github_reconnect_required', str(exc)) from exc

        user = github_token_update_from_data(user=user, token_data=token_data)

    return user.access_token
