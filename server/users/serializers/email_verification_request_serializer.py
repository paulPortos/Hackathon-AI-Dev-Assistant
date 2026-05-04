from rest_framework import serializers


class EmailVerificationRequestSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
