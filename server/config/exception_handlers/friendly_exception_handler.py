import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback


_LOGGER = logging.getLogger('api.errors')


def friendly_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None and response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
        return response

    request = context.get('request')
    django_request = getattr(request, '_request', request)
    request_id = getattr(django_request, 'request_id', '')
    user = getattr(django_request, 'user', None)
    view = context.get('view')
    user_id = None

    if user:
        try:
            user_id = getattr(user, 'id', None) if user.is_authenticated else None
        except AttributeError:
            user_id = None

    set_rollback()
    _LOGGER.exception(
        'unhandled_api_exception',
        extra={
            'request_id': request_id,
            'method': getattr(django_request, 'method', ''),
            'path': getattr(django_request, 'path', ''),
            'user_id': user_id,
            'view': view.__class__.__name__ if view else '',
            'exception_class': exc.__class__.__name__,
        },
    )

    return Response(
        {
            'detail': 'Something went wrong. Please try again.',
            'code': 'server_error',
            'request_id': request_id,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
