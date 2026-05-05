from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from multi_agent.selectors import senior_dev_finding_list, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevFindingSerializer
from multi_agent.models import SeniorDevFinding


class SeniorDevFindingListView(GenericAPIView):
    serializer_class = SeniorDevFindingSerializer

    def get(self, request, session_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev session does not exist') from exc

        queryset = senior_dev_finding_list(session)

        finding_type = request.query_params.get('type')
        if finding_type:
            finding_type = str(finding_type).strip().lower()
            valid_types = {choice for choice, _ in SeniorDevFinding.FindingType.choices}
            if finding_type not in valid_types:
                raise ValidationError({'type': 'Invalid finding type'})
            queryset = queryset.filter(finding_type=finding_type)

        severity = request.query_params.get('severity')
        if severity:
            severity = str(severity).strip().lower()
            valid_severities = {choice for choice, _ in SeniorDevFinding.Severity.choices}
            if severity not in valid_severities:
                raise ValidationError({'severity': 'Invalid severity'})
            queryset = queryset.filter(severity=severity)

        status = request.query_params.get('status')
        if status:
            status = str(status).strip().lower()
            valid_statuses = {choice for choice, _ in SeniorDevFinding.Status.choices}
            if status not in valid_statuses:
                raise ValidationError({'status': 'Invalid status'})
            queryset = queryset.filter(status=status)

        message_id = request.query_params.get('message_id')
        if message_id:
            try:
                message_id = int(message_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError({'message_id': 'Must be an integer'}) from exc
            queryset = queryset.filter(message_id=message_id)

        claim_id = request.query_params.get('claim_id')
        if claim_id:
            try:
                claim_id = int(claim_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError({'claim_id': 'Must be an integer'}) from exc
            queryset = queryset.filter(claim_id=claim_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)
