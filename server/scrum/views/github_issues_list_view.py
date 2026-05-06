from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from projects.models.project import Project
from scrum.models.github_issue import GitHubIssue
from rest_framework import serializers

class GitHubIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIssue
        fields = '__all__'

class GitHubIssuesListView(APIView):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        state = request.query_params.get('state', 'open')
        
        issues = GitHubIssue.objects.filter(project=project, state=state).order_by('-github_number')
        serializer = GitHubIssueSerializer(issues, many=True)
        return Response(serializer.data)
