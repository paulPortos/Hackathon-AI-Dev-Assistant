from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from scrum.models.scrum_session import ScrumSession
from scrum.models.scrum_message import ScrumMessage
from scrum.serializers.scrum_serializers import ScrumSessionSerializer, ScrumMessageSerializer


class ScrumSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ScrumSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ScrumSession.objects.filter(user=self.request.user)
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None, **kwargs):
        session = self.get_object()
        messages = session.messages.all().order_by('created_at')
        serializer = ScrumMessageSerializer(messages, many=True)
        return Response(serializer.data)
