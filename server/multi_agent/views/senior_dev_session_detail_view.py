from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from multi_agent.selectors import senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevSessionSerializer, SeniorDevSessionUpdateSerializer


class SeniorDevSessionDetailView(APIView):
    def get(self, request, session_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev session does not exist') from exc

        return Response(SeniorDevSessionSerializer(session).data)

    def patch(self, request, session_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev session does not exist') from exc

        serializer = SeniorDevSessionUpdateSerializer(session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(SeniorDevSessionSerializer(session).data)
