from django.contrib.auth import get_user_model


def user_get_by_id(user_id):
    user_model = get_user_model()
    return user_model.objects.get(id=user_id)
