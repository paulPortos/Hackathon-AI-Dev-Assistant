from rest_framework import serializers

from multi_agent.models import SeniorDevFinding


class SeniorDevFindingSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='finding_type', read_only=True)

    class Meta:
        model = SeniorDevFinding
        fields = (
            'id',
            'session_id',
            'message_id',
            'claim_id',
            'type',
            'title',
            'category',
            'severity',
            'confidence_score',
            'confidence_reason',
            'evidence',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
