from rest_framework import serializers

from projects.models import ProjectAuditLog


class ProjectAuditLogSerializer(serializers.ModelSerializer):
    actor_user_id = serializers.IntegerField(source='actor_user.id', read_only=True)
    actor_username = serializers.CharField(source='actor_user.username', read_only=True)
    actor_name = serializers.CharField(source='actor_user.name', read_only=True)

    class Meta:
        model = ProjectAuditLog
        fields = (
            'id',
            'project_id',
            'actor_user_id',
            'actor_username',
            'actor_name',
            'actor_agent',
            'event_type',
            'target_type',
            'target_id',
            'summary',
            'before',
            'after',
            'created_at',
        )
        read_only_fields = fields
