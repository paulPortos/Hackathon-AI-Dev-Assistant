from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from projects.selectors import project_get_for_member, project_task_list
from projects.serializers import ProjectTaskSerializer


class ProjectTaskListView(GenericAPIView):
    serializer_class = ProjectTaskSerializer

    def get(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        queryset = project_task_list(project)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)
