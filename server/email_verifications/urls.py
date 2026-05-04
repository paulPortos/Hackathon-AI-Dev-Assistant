from django.urls import path

from email_verifications.views import EmailVerificationConfirmView, EmailVerificationRequestView


app_name = 'email_verifications'

urlpatterns = [
    path('request/', EmailVerificationRequestView.as_view(), name='email-verification-request'),
    path('confirm/', EmailVerificationConfirmView.as_view(), name='email-verification-confirm'),
]
