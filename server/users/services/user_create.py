from django.contrib.auth import get_user_model


def user_create(*, github_id, username, name='', email='', avatar_url='', access_token='', **extra_fields):
    user_model = get_user_model()
    return user_model.objects.create_user(
        github_id=str(github_id),
        username=username,
        name=name or '',
        email=email or '',
        avatar_url=avatar_url or '',
        access_token=access_token or '',
        **extra_fields,
    )
