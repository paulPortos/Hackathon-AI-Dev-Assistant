from rest_framework import serializers

from multi_agent.models import SeniorDevMessage


class SeniorDevMessageCreateSerializer(serializers.Serializer):
    input_type = serializers.ChoiceField(choices=SeniorDevMessage.InputType.choices)
    text = serializers.CharField(required=False, allow_blank=True)
    choice = serializers.CharField(required=False, allow_blank=True)
    choice_payload = serializers.JSONField(required=False)
    audio = serializers.FileField(required=False)
