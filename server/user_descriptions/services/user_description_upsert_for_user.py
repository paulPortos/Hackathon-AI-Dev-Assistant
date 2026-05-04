from django.db import transaction

from user_descriptions.models import UserDescription
from user_descriptions.services.user_description_update import user_description_update


@transaction.atomic
def user_description_upsert_for_user(*, user, data):
    user_description, created = UserDescription.objects.select_for_update().get_or_create(user=user)
    if created:
        return user_description_update(user_description=user_description, data=data)
    return user_description_update(user_description=user_description, data=data)
