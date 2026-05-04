import re
import uuid


_REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._:-]{1,128}$')


class RequestIdMiddleware:
    header_name = 'HTTP_X_REQUEST_ID'
    response_header_name = 'X-Request-ID'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name)
        if not request_id or not _REQUEST_ID_PATTERN.match(request_id):
            request_id = str(uuid.uuid4())

        request.request_id = request_id
        response = self.get_response(request)
        response[self.response_header_name] = request_id
        return response
