from rest_framework import serializers

from multi_agent.models import SeniorDevClaim


class SeniorDevClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeniorDevClaim
        fields = (
            'id',
            'session_id',
            'message_id',
            'text',
            'category',
            'status',
            'evidence',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
