import logging
import time

from config.middleware.suspicious_input_detector import SuspiciousInputDetector


_SECURITY_AUDIT_LOGGER = logging.getLogger('security.audit')
_SUSPICIOUS_INPUT_LOGGER = logging.getLogger('security.suspicious_input')


class SecurityAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_input_detector = SuspiciousInputDetector()

    def __call__(self, request):
        started_at = time.perf_counter()
        suspicious_signals = self.suspicious_input_detector.detect(request)

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            self._log_request(
                request=request,
                status_code=500,
                duration_ms=duration_ms,
                suspicious_signals=suspicious_signals,
                exception=exc,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        self._log_request(
            request=request,
            status_code=response.status_code,
            duration_ms=duration_ms,
            suspicious_signals=suspicious_signals,
        )
        return response

    def _log_request(self, request, status_code, duration_ms, suspicious_signals, exception=None):
        extra = self._build_extra(
            request=request,
            status_code=status_code,
            duration_ms=duration_ms,
            suspicious_signals=suspicious_signals,
        )

        if exception:
            extra['exception_class'] = exception.__class__.__name__
            _SECURITY_AUDIT_LOGGER.exception('request_exception', extra=extra)
        else:
            _SECURITY_AUDIT_LOGGER.info('request_completed', extra=extra)

        if suspicious_signals:
            _SUSPICIOUS_INPUT_LOGGER.warning(
                'suspicious_input_detected',
                extra={
                    'request_id': getattr(request, 'request_id', ''),
                    'method': request.method,
                    'path': request.path,
                    'status_code': status_code,
                    'user_id': self._user_id(request),
                    'client_ip': self._client_ip(request),
                    'signals': suspicious_signals,
                },
            )

    def _build_extra(self, request, status_code, duration_ms, suspicious_signals):
        resolver_match = getattr(request, 'resolver_match', None)
        return {
            'request_id': getattr(request, 'request_id', ''),
            'method': request.method,
            'path': request.path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user_id': self._user_id(request),
            'client_ip': self._client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'view_name': getattr(resolver_match, 'view_name', '') if resolver_match else '',
            'url_name': getattr(resolver_match, 'url_name', '') if resolver_match else '',
            'app_names': getattr(resolver_match, 'app_names', []) if resolver_match else [],
            'namespaces': getattr(resolver_match, 'namespaces', []) if resolver_match else [],
            'route': getattr(resolver_match, 'route', '') if resolver_match else '',
            'suspicious_input_count': len(suspicious_signals),
        }

    def _client_ip(self, request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',', 1)[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _user_id(self, request):
        user = getattr(request, 'user', None)
        if not user:
            return None

        try:
            if not user.is_authenticated:
                return None
        except AttributeError:
            return None

        return getattr(user, 'id', None)
