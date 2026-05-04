from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.selectors import project_get_for_member, project_member_get_for_project
from projects.serializers import ProjectMemberRoleSerializer, ProjectMemberSerializer
from projects.services import project_member_delete, project_member_update


class ProjectMemberDetailView(APIView):
    def patch(self, request, project_id, member_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            project_member = project_member_get_for_project(project=project, member_id=member_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project member does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can update members')

        serializer = ProjectMemberRoleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        project_member = project_member_update(project_member=project_member, data=serializer.validated_data)
        return Response(ProjectMemberSerializer(project_member).data)

    def delete(self, request, project_id, member_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            project_member = project_member_get_for_project(project=project, member_id=member_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project member does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can remove members')

        try:
            project_member_delete(project_member=project_member)
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)
