from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from user_descriptions.selectors import user_description_get_for_user
from user_descriptions.serializers import UserDescriptionSerializer
from user_descriptions.services import user_description_upsert_for_user


class UserDescriptionMeView(APIView):
    def get(self, request, version=None):
        try:
            user_description = user_description_get_for_user(request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('User description does not exist') from exc

        return Response(UserDescriptionSerializer(user_description).data)

    def patch(self, request, version=None):
        try:
            user_description = user_description_get_for_user(request.user)
        except ObjectDoesNotExist:
            user_description = None

        serializer = UserDescriptionSerializer(user_description, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user_description = user_description_upsert_for_user(user=request.user, data=serializer.validated_data)
        return Response(UserDescriptionSerializer(user_description).data)
