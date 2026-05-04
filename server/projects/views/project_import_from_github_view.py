from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.providers import GitHubRepositoryError
from projects.serializers import ProjectImportFromGitHubSerializer, ProjectSerializer
from projects.services import project_import_from_github


class ProjectImportFromGitHubView(APIView):
    def post(self, request, version=None):
        serializer = ProjectImportFromGitHubSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = project_import_from_github(
                creator=request.user,
                repository=serializer.validated_data['repository'],
            )
        except GitHubRepositoryError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        return Response(ProjectSerializer(project).data)
