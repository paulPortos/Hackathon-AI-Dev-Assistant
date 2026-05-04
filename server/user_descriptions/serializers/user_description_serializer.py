from rest_framework import serializers

from user_descriptions.models import UserDescription


class UserDescriptionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserDescription
        fields = (
            'id',
            'user_id',
            'username',
            'name',
            'email',
            'primary_role',
            'experience_level',
            'summary',
            'skills',
            'preferred_tasks',
            'avoided_tasks',
            'availability_notes',
            'agent_notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'username', 'name', 'email', 'created_at', 'updated_at')

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Skills must be a list')

        normalized_skills = []
        for skill in value:
            if not isinstance(skill, dict):
                raise serializers.ValidationError('Each skill must be an object')

            name = str(skill.get('name', '')).strip()
            level = skill.get('level')
            if not name:
                raise serializers.ValidationError('Each skill must include a name')
            if not isinstance(level, int) or level < 1 or level > 5:
                raise serializers.ValidationError('Each skill level must be an integer from 1 to 5')

            normalized_skills.append({'name': name, 'level': level})

        return normalized_skills

    def validate_preferred_tasks(self, value):
        return self._validate_task_list(value)

    def validate_avoided_tasks(self, value):
        return self._validate_task_list(value)

    def _validate_task_list(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Task values must be a list')

        normalized_tasks = []
        seen_tasks = set()
        for task in value:
            normalized_task = str(task).strip()
            if not normalized_task:
                raise serializers.ValidationError('Task values cannot be blank')
            if normalized_task not in seen_tasks:
                normalized_tasks.append(normalized_task)
                seen_tasks.add(normalized_task)

        return normalized_tasks
