from rest_framework import serializers


class ProjectRepositoryBranchSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    commit_sha = serializers.CharField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
