from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from multi_agent.selectors import senior_dev_finding_get_for_session, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevFindingSerializer, SeniorDevFindingStatusUpdateSerializer
from multi_agent.services import senior_dev_finding_status_update


class SeniorDevFindingDetailView(GenericAPIView):
    serializer_class = SeniorDevFindingSerializer

    def patch(self, request, session_id, finding_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
            finding = senior_dev_finding_get_for_session(session=session, finding_id=finding_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev finding does not exist') from exc

        serializer = SeniorDevFindingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        finding = senior_dev_finding_status_update(finding=finding, status=serializer.validated_data['status'])
        return Response(self.get_serializer(finding).data)
