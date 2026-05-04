from user_descriptions.models import UserDescription


def user_description_get_by_id(user_description_id):
    return UserDescription.objects.select_related('user').get(id=user_description_id)
