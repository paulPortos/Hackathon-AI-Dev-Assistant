from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'github_id',
            'username',
            'name',
            'email',
            'email_verified_at',
            'avatar_url',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
