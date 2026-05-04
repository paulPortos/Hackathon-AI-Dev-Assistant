from django.contrib.auth import get_user_model


def user_get_by_github_id(github_id):
    user_model = get_user_model()
    return user_model.objects.get(github_id=str(github_id))
