from user_descriptions.models import UserDescription


def user_description_list():
    return UserDescription.objects.select_related('user').all()
