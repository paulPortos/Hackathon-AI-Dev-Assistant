from rest_framework import serializers

from projects.serializers.project_repository_branch_serializer import ProjectRepositoryBranchSerializer


class ProjectRepositoryBranchListSerializer(serializers.Serializer):
    default_branch = serializers.CharField(read_only=True)
    branches = ProjectRepositoryBranchSerializer(many=True, read_only=True)
