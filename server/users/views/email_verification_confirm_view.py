from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import EmailVerificationConfirmSerializer
from users.services import email_verification_confirm_for_user
from users.serializers import UserSerializer


class EmailVerificationConfirmView(APIView):
    def post(self, request, version=None):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = email_verification_confirm_for_user(user=request.user, code=serializer.validated_data['code'])
        except DjangoValidationError as exc:
            raise ValidationError({'detail': exc.message}) from exc

        return Response({'detail': 'Email verified', 'user': UserSerializer(user).data}, status=status.HTTP_200_OK)
