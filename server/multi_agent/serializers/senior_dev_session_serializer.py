from rest_framework import serializers

from multi_agent.models import SeniorDevSession


class SeniorDevSessionSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.github_full_name', read_only=True)

    class Meta:
        model = SeniorDevSession
        fields = (
            'id',
            'project_id',
            'project_name',
            'user_id',
            'name',
            'commit_sha',
            'branch_name',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
