from rest_framework import serializers

from users.models import User


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'name',
            'avatar_url',
        )
        read_only_fields = fields
