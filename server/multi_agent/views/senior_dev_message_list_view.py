from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from multi_agent.agents.sr_dev.workflows import senior_dev_message_process
from multi_agent.selectors import senior_dev_message_list, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevMessageCreateSerializer, SeniorDevMessageSerializer


class SeniorDevMessageListView(GenericAPIView):
    serializer_class = SeniorDevMessageSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, session_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev session does not exist') from exc

        queryset = senior_dev_message_list(session)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)

    def post(self, request, session_id, version=None):
        try:
            session = senior_dev_session_get_for_user(session_id=session_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Senior Dev session does not exist') from exc

        serializer = SeniorDevMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = senior_dev_message_process(
                session=session,
                user=request.user,
                input_type=serializer.validated_data['input_type'],
                text=serializer.validated_data.get('text', ''),
                choice=serializer.validated_data.get('choice', ''),
                choice_payload=serializer.validated_data.get('choice_payload'),
                audio_file=serializer.validated_data.get('audio'),
            )
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(payload)
