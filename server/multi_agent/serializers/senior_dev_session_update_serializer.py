from rest_framework import serializers

from multi_agent.models import SeniorDevSession


class SeniorDevSessionUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = SeniorDevSession
        fields = ('name',)
