from django.http import HttpResponse
from django.views.decorators.http import require_safe


@require_safe
def health_check_view(request, version=None):
    response = HttpResponse(status=204)
    response['Cache-Control'] = 'no-store'
    response['X-Health-Check'] = 'ok'
    return response
