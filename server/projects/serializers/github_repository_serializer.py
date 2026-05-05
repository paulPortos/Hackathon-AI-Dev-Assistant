from rest_framework import serializers


class GitHubRepositorySerializer(serializers.Serializer):
    github_repo_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    owner_login = serializers.CharField(read_only=True)
    owner_avatar_url = serializers.URLField(read_only=True)
    html_url = serializers.URLField(read_only=True)
    clone_url = serializers.URLField(read_only=True)
    default_branch = serializers.CharField(read_only=True)
    visibility = serializers.CharField(read_only=True)
    primary_language = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_private = serializers.BooleanField(read_only=True)
    is_fork = serializers.BooleanField(read_only=True)
    is_archived = serializers.BooleanField(read_only=True)
    updated_at = serializers.CharField(read_only=True, allow_null=True)
