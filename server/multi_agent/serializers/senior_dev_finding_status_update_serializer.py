from rest_framework import serializers

from multi_agent.models import SeniorDevFinding


class SeniorDevFindingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SeniorDevFinding.Status.choices)
