from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.selectors import project_get_for_member, project_meeting_settings_get_for_project
from projects.serializers import ProjectMeetingSettingsSerializer
from projects.services import project_meeting_settings_upsert


class ProjectMeetingSettingsView(APIView):
    def get(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            meeting_settings = project_meeting_settings_get_for_project(project)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project meeting settings do not exist') from exc

        return Response(ProjectMeetingSettingsSerializer(meeting_settings).data)

    def put(self, request, project_id, version=None):
        return self._upsert(request=request, project_id=project_id, partial=False)

    def patch(self, request, project_id, version=None):
        return self._upsert(request=request, project_id=project_id, partial=True)

    def _upsert(self, *, request, project_id, partial):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can update meeting settings')

        try:
            meeting_settings = project_meeting_settings_get_for_project(project)
        except ObjectDoesNotExist:
            meeting_settings = None
            partial = False

        serializer = ProjectMeetingSettingsSerializer(meeting_settings, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        meeting_settings = project_meeting_settings_upsert(project=project, data=serializer.validated_data)
        return Response(ProjectMeetingSettingsSerializer(meeting_settings).data)
