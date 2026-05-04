from rest_framework import serializers


class EmailVerificationConfirmSerializer(serializers.Serializer):
    code = serializers.RegexField(regex=r'^\d{6}$', max_length=6, min_length=6)
