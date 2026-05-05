from rest_framework import serializers

from multi_agent.models import SeniorDevMessage


class SeniorDevMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeniorDevMessage
        fields = (
            'id',
            'session_id',
            'source_user_message_id',
            'role',
            'input_type',
            'text_content',
            'structured_payload',
            'created_at',
        )
        read_only_fields = fields
