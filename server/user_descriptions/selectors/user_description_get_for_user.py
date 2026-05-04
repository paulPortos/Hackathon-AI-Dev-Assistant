from user_descriptions.models import UserDescription


def user_description_get_for_user(user):
    return UserDescription.objects.select_related('user').get(user=user)
