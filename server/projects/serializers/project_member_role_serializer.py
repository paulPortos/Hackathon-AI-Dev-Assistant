from rest_framework import serializers


class ProjectMemberRoleSerializer(serializers.Serializer):
    display_role = serializers.CharField(max_length=255, required=False)
    roles = serializers.JSONField(required=False)

    def validate_roles(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Roles must be a list')

        normalized_roles = []
        seen_roles = set()
        for role in value:
            normalized_role = str(role).strip()
            if not normalized_role:
                raise serializers.ValidationError('Roles cannot include blank values')
            if normalized_role not in seen_roles:
                normalized_roles.append(normalized_role)
                seen_roles.add(normalized_role)

        return normalized_roles
