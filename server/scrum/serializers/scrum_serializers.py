from rest_framework import serializers
from scrum.models.scrum_session import ScrumSession
from scrum.models.scrum_message import ScrumMessage


class ScrumMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrumMessage
        fields = ['id', 'role', 'input_type', 'text_content', 'structured_payload', 'created_at']


class ScrumSessionSerializer(serializers.ModelSerializer):
    messages = ScrumMessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = ScrumSession
        fields = ['id', 'project', 'user', 'status', 'created_at', 'updated_at', 'message_count', 'messages']
        read_only_fields = ['user', 'created_at', 'updated_at']
