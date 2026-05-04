from rest_framework import serializers

from projects.models import ProjectMember


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    avatar_url = serializers.URLField(source='user.avatar_url', read_only=True)
    invited_by_id = serializers.IntegerField(source='invited_by.id', read_only=True)

    class Meta:
        model = ProjectMember
        fields = (
            'id',
            'project_id',
            'user_id',
            'username',
            'name',
            'avatar_url',
            'invited_by_id',
            'display_role',
            'roles',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
