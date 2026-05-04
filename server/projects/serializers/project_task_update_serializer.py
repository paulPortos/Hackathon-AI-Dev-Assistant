from rest_framework import serializers

from projects.models import ProjectTask


class ProjectTaskUpdateSerializer(serializers.Serializer):
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    related_finding_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=ProjectTask.Category.choices, required=False)
    priority = serializers.ChoiceField(choices=ProjectTask.Priority.choices, required=False)
    status = serializers.ChoiceField(choices=ProjectTask.Status.choices, required=False)
    created_by_agent = serializers.CharField(max_length=255, required=False, allow_blank=True)
    reasoning = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)
