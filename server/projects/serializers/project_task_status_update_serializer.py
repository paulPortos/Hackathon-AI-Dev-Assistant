from rest_framework import serializers

from projects.models import ProjectTask


class ProjectTaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProjectTask.Status.choices)
