from rest_framework import serializers

from multi_agent.models import SeniorDevToolCall


class SeniorDevToolCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeniorDevToolCall
        fields = (
            'id',
            'session_id',
            'message_id',
            'tool_name',
            'safe_input_summary',
            'safe_result_summary',
            'status',
            'duration_ms',
            'error_code',
            'commit_sha',
            'created_at',
        )
        read_only_fields = fields
