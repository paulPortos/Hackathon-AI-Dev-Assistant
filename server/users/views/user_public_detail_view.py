from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.selectors import user_get_by_id
from users.serializers import PublicUserSerializer


class UserPublicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, version=None):
        try:
            user = user_get_by_id(user_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('User does not exist') from exc

        return Response(PublicUserSerializer(user).data)
