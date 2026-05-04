import re

from rest_framework import serializers


class ProjectImportFromGitHubSerializer(serializers.Serializer):
    repository = serializers.CharField(max_length=255)

    def validate_repository(self, value):
        repository = value.strip()
        if not re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', repository):
            raise serializers.ValidationError('Repository must use owner/name format')
        return repository
