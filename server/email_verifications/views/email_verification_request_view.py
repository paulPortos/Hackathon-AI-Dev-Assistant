from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from email_verifications.providers import EmailDeliveryError
from email_verifications.services import email_verification_request_for_user


class EmailVerificationRequestView(APIView):
    def post(self, request, version=None):
        try:
            email_verification_request_for_user(user=request.user)
        except EmailDeliveryError as exc:
            raise ValidationError({'detail': str(exc)}) from exc
        except DjangoValidationError as exc:
            raise ValidationError({'detail': exc.message}) from exc

        return Response({'detail': 'Verification code sent'}, status=status.HTTP_200_OK)
