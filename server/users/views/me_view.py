from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, version=None):
        return Response(UserSerializer(request.user).data)
