from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from multi_agent.selectors import senior_dev_session_list_for_user
from multi_agent.serializers import SeniorDevSessionCreateSerializer, SeniorDevSessionSerializer
from multi_agent.services import senior_dev_session_create


class SeniorDevSessionListView(GenericAPIView):
    serializer_class = SeniorDevSessionSerializer

    def get(self, request, version=None):
        queryset = senior_dev_session_list_for_user(request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)

    def post(self, request, version=None):
        serializer = SeniorDevSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            session = senior_dev_session_create(user=request.user, **serializer.validated_data)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(SeniorDevSessionSerializer(session).data)
