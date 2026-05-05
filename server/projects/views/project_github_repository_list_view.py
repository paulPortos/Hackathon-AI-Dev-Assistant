from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from projects.providers import GitHubRepositoryError
from projects.serializers import GitHubRepositorySerializer
from projects.services import project_github_repository_list
from users.services import GitHubTokenError


class ProjectGitHubRepositoryListView(GenericAPIView):
    serializer_class = GitHubRepositorySerializer

    def get(self, request, version=None):
        try:
            repositories = project_github_repository_list(request.user)
        except GitHubRepositoryError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        except GitHubTokenError as exc:
            raise ValidationError({'detail': str(exc), 'code': exc.code}) from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        page = self.paginate_queryset(repositories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(repositories, many=True).data)
