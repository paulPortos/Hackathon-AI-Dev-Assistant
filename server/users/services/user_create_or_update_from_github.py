from django.contrib.auth import get_user_model
from django.db import transaction

from users.services.user_update import user_update


@transaction.atomic
def user_create_or_update_from_github(*, github_user, access_token, email=''):
    github_id = github_user.get('id')
    username = github_user.get('login')

    if not github_id:
        raise ValueError('GitHub response did not include an id')
    if not username:
        raise ValueError('GitHub response did not include a login')

    defaults = {
        'username': username,
        'name': github_user.get('name') or '',
        'email': email or github_user.get('email') or '',
        'avatar_url': github_user.get('avatar_url') or '',
        'access_token': access_token,
    }

    user_model = get_user_model()
    user, created = user_model.objects.select_for_update().get_or_create(
        github_id=str(github_id),
        defaults=defaults,
    )
    if not created:
        user_update(user=user, **defaults)

    return user
