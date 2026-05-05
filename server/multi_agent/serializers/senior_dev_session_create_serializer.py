from rest_framework import serializers


class SeniorDevSessionCreateSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    commit_sha = serializers.CharField(max_length=255)
    branch_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
