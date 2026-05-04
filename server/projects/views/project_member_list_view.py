from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from projects.selectors import project_get_for_member, project_member_list
from projects.serializers import ProjectMemberInviteSerializer, ProjectMemberSerializer
from projects.services import project_member_invite
from users.selectors import user_get_by_id


class ProjectMemberListView(GenericAPIView):
    serializer_class = ProjectMemberSerializer

    def get(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        queryset = project_member_list(project)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)

    def post(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can invite members')

        serializer = ProjectMemberInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = user_get_by_id(serializer.validated_data['user_id'])
            project_member = project_member_invite(
                project=project,
                user=user,
                invited_by=request.user,
                display_role=serializer.validated_data['display_role'],
                roles=serializer.validated_data['roles'],
            )
        except ObjectDoesNotExist as exc:
            raise NotFound('User does not exist') from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(ProjectMemberSerializer(project_member).data)
