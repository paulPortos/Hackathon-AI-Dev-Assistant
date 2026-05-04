from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from user_descriptions.selectors import user_description_get_for_user
from user_descriptions.serializers import UserDescriptionSerializer
from users.selectors import user_get_by_id


class UserDescriptionForUserView(APIView):
    def get(self, request, user_id, version=None):
        try:
            user = user_get_by_id(user_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('User does not exist') from exc

        try:
            user_description = user_description_get_for_user(user)
        except ObjectDoesNotExist as exc:
            raise NotFound('User description does not exist') from exc

        return Response(UserDescriptionSerializer(user_description).data)
