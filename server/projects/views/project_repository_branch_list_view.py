from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.providers import GitHubRepositoryError
from projects.selectors import project_get_for_member
from projects.serializers import ProjectRepositoryBranchListSerializer
from projects.services import project_repository_branch_list
from users.services import GitHubTokenError


class ProjectRepositoryBranchListView(APIView):
    def get(self, request, project_id, version=None):
        try:
            project = project_get_for_member(project_id=project_id, user=request.user)
        except ObjectDoesNotExist as exc:
            raise NotFound('Project does not exist') from exc

        try:
            branch_context = project_repository_branch_list(project)
        except GitHubRepositoryError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        except GitHubTokenError as exc:
            raise ValidationError({'detail': str(exc), 'code': exc.code}) from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(ProjectRepositoryBranchListSerializer(branch_context).data)
