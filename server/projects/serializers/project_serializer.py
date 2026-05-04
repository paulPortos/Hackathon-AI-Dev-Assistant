from rest_framework import serializers

from projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)

    class Meta:
        model = Project
        fields = (
            'id',
            'creator_id',
            'creator_username',
            'github_repo_id',
            'github_full_name',
            'github_html_url',
            'github_clone_url',
            'github_default_branch',
            'github_visibility',
            'github_primary_language',
            'github_languages',
            'github_description',
            'github_is_private',
            'overview',
            'goals',
            'tech_stack',
            'business_context',
            'agent_notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'creator_id',
            'creator_username',
            'github_repo_id',
            'github_full_name',
            'github_html_url',
            'github_clone_url',
            'github_default_branch',
            'github_visibility',
            'github_primary_language',
            'github_languages',
            'github_description',
            'github_is_private',
            'created_at',
            'updated_at',
        )

    def validate_tech_stack(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Tech stack must be a list')

        normalized_items = []
        seen_items = set()
        for item in value:
            normalized_item = str(item).strip()
            if not normalized_item:
                raise serializers.ValidationError('Tech stack values cannot be blank')
            if normalized_item not in seen_items:
                normalized_items.append(normalized_item)
                seen_items.add(normalized_item)

        return normalized_items
