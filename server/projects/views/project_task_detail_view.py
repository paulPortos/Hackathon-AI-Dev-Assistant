from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.selectors import (
    project_get_for_member,
    project_member_get_for_project,
    project_task_get_for_project,
    project_vulnerability_get_for_project,
)
from projects.serializers import ProjectTaskSerializer, ProjectTaskStatusUpdateSerializer, ProjectTaskUpdateSerializer
from projects.services import project_task_delete, project_task_status_update, project_task_update


class ProjectTaskDetailView(APIView):
    def get(self, request, project_id, task_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            project_task = project_task_get_for_project(project=project, task_id=task_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project task does not exist') from exc

        return Response(ProjectTaskSerializer(project_task).data)

    def patch(self, request, project_id, task_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            project_task = project_task_get_for_project(project=project, task_id=task_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project task does not exist') from exc

        if project.creator_id == request.user.id:
            serializer = ProjectTaskUpdateSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            data = dict(serializer.validated_data)
            assigned_to_id = data.pop('assigned_to_id', None)
            related_finding_id = data.pop('related_finding_id', None)

            try:
                if 'assigned_to_id' in serializer.validated_data:
                    data['assigned_to'] = (
                        project_member_get_for_project(project=project, member_id=assigned_to_id)
                        if assigned_to_id is not None
                        else None
                    )
                if 'related_finding_id' in serializer.validated_data:
                    data['related_finding'] = (
                        project_vulnerability_get_for_project(project=project, vulnerability_id=related_finding_id)
                        if related_finding_id is not None
                        else None
                    )
            except ObjectDoesNotExist as exc:
                raise NotFound('Related project resource does not exist') from exc

            try:
                project_task = project_task_update(project_task=project_task, data=data, actor_user=request.user)
            except ValueError as exc:
                raise ValidationError({'detail': str(exc)}) from exc
            return Response(ProjectTaskSerializer(project_task).data)

        if project_task.assigned_to and project_task.assigned_to.user_id == request.user.id:
            if set(request.data.keys()) != {'status'}:
                raise PermissionDenied('Assigned members can only update task status')
            serializer = ProjectTaskStatusUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            project_task = project_task_status_update(
                project_task=project_task,
                status=serializer.validated_data['status'],
                actor_user=request.user,
            )
            return Response(ProjectTaskSerializer(project_task).data)

        raise PermissionDenied('Only project creator or assigned member can update task')

    def delete(self, request, project_id, task_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
            project_task = project_task_get_for_project(project=project, task_id=task_id)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project task does not exist') from exc

        if project.creator_id != request.user.id:
            raise PermissionDenied('Only project creator can delete task')

        project_task_delete(project_task=project_task, actor_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
