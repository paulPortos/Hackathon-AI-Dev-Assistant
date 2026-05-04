from rest_framework import serializers

from projects.models import ProjectTask


class ProjectTaskSerializer(serializers.ModelSerializer):
    assigned_to_user_id = serializers.IntegerField(source='assigned_to.user.id', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.user.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.name', read_only=True)

    class Meta:
        model = ProjectTask
        fields = (
            'id',
            'project_id',
            'assigned_to_id',
            'assigned_to_user_id',
            'assigned_to_username',
            'assigned_to_name',
            'related_finding_id',
            'title',
            'description',
            'category',
            'priority',
            'status',
            'created_by_agent',
            'reasoning',
            'due_date',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
