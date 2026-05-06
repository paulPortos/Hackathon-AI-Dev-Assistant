from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from projects.models.project import Project
from projects.services.github_issues_sync import github_issues_sync

class GitHubIssuesSyncView(APIView):
    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        try:
            result = github_issues_sync(project, request.user)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
