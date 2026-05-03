from django.contrib.auth import get_user_model


User = get_user_model()


def user_get_by_id(user_id):
    return User.objects.get(id=user_id)


def user_get_by_github_id(github_id):
    return User.objects.get(github_id=str(github_id))
