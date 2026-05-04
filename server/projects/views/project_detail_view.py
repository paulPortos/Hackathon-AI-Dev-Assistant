from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.selectors import project_get_for_member
from projects.serializers import ProjectSerializer
from projects.services import project_update_context


class ProjectDetailView(APIView):
    def get(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        return Response(ProjectSerializer(project).data)

    def patch(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can update project')

        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        project = project_update_context(project=project, data=serializer.validated_data)
        return Response(ProjectSerializer(project).data)
