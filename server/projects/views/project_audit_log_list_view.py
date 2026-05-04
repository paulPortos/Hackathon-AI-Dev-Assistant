from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView

from projects.selectors import project_audit_log_list, project_get_for_member
from projects.serializers import ProjectAuditLogSerializer


class ProjectAuditLogListView(ListAPIView):
    serializer_class = ProjectAuditLogSerializer

    def get_queryset(self):
        try:
            project = project_get_for_member(project_id=self.kwargs['project_id'], user=self.request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        return project_audit_log_list(project)
