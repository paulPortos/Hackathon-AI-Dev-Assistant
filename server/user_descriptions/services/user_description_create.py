from user_descriptions.models import UserDescription


def user_description_create(*, user, data):
    return UserDescription.objects.create(user=user, **data)
