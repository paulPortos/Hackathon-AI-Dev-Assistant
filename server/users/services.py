from django.contrib.auth import get_user_model
from django.db import transaction


User = get_user_model()


def user_create(*, github_id, username, name='', email='', avatar_url='', access_token='', **extra_fields):
    return User.objects.create_user(
        github_id=str(github_id),
        username=username,
        name=name or '',
        email=email or '',
        avatar_url=avatar_url or '',
        access_token=access_token or '',
        **extra_fields,
    )


def user_update(*, user, **fields):
    allowed_fields = {'github_id', 'username', 'name', 'email', 'avatar_url', 'access_token', 'is_active', 'is_staff'}
    update_fields = []

    for field, value in fields.items():
        if field not in allowed_fields:
            continue
        setattr(user, field, value if value is not None else '')
        update_fields.append(field)

    if update_fields:
        user.save(update_fields=[*update_fields, 'updated_at'])

    return user


def user_delete(*, user):
    user.delete()


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

    user, created = User.objects.select_for_update().get_or_create(
        github_id=str(github_id),
        defaults=defaults,
    )
    if not created:
        user_update(user=user, **defaults)

    return user
