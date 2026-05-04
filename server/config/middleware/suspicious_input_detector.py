import json
import re

from django.conf import settings
from django.http import QueryDict
from django.http.request import RawPostDataException


_SQL_PATTERNS = (
    ('sql_comment', re.compile(r'(--|#|/\*)')),
    ('union_select', re.compile(r'\bunion\b\s+(?:all\s+)?\bselect\b', re.IGNORECASE)),
    ('boolean_tautology', re.compile(r"""(?:'|")?\s*(?:or|and)\s+(?:'|")?\w+(?:'|")?\s*=\s*(?:'|")?\w+""", re.IGNORECASE)),
    ('stacked_statement', re.compile(r';\s*(?:drop|delete|insert|update|alter|create|truncate)\b', re.IGNORECASE)),
    ('dangerous_statement', re.compile(r'\b(?:drop|truncate|alter)\s+(?:table|database)\b', re.IGNORECASE)),
    ('time_based', re.compile(r'\b(?:sleep|benchmark|pg_sleep)\s*\(', re.IGNORECASE)),
    ('sql_metadata', re.compile(r'\b(?:information_schema|pg_catalog|sysobjects|xp_cmdshell)\b', re.IGNORECASE)),
)
_SENSITIVE_FIELD_MARKERS = (
    'authorization',
    'access_token',
    'refresh',
    'token',
    'password',
    'secret',
    'api_key',
    'apikey',
    'cookie',
)


class SuspiciousInputDetector:
    json_content_type = 'application/json'
    form_content_type = 'application/x-www-form-urlencoded'

    def __init__(self):
        self.body_max_bytes = settings.SECURITY_AUDIT_BODY_MAX_BYTES
        self.max_signals = settings.SECURITY_AUDIT_MAX_SUSPICIOUS_SIGNALS

    def detect(self, request):
        signals = []
        self._inspect_query_params(request, signals)
        self._inspect_body(request, signals)
        return signals

    def _inspect_query_params(self, request, signals):
        for field_name, values in request.GET.lists():
            for value in values:
                self._append_signal(signals, source='query', field_path=field_name, value=value)

    def _inspect_body(self, request, signals):
        content_type = request.META.get('CONTENT_TYPE', '').split(';', 1)[0].strip().lower()
        if content_type not in {self.json_content_type, self.form_content_type}:
            return

        try:
            content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            return

        if content_length <= 0 or content_length > self.body_max_bytes:
            return

        try:
            body = request.body
        except RawPostDataException:
            return

        if not body:
            return

        if content_type == self.json_content_type:
            try:
                payload = json.loads(body.decode(request.encoding or 'utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return
            self._inspect_json_value(signals, payload, 'body')
            return

        try:
            query_dict = QueryDict(body.decode(request.encoding or 'utf-8'), encoding=request.encoding or 'utf-8')
        except UnicodeDecodeError:
            return

        for field_name, values in query_dict.lists():
            for value in values:
                self._append_signal(signals, source='body', field_path=field_name, value=value)

    def _inspect_json_value(self, signals, value, field_path):
        if len(signals) >= self.max_signals:
            return

        if isinstance(value, dict):
            for key, child_value in value.items():
                child_path = f'{field_path}.{key}'
                self._inspect_json_value(signals, child_value, child_path)
            return

        if isinstance(value, list):
            for index, child_value in enumerate(value):
                child_path = f'{field_path}[{index}]'
                self._inspect_json_value(signals, child_value, child_path)
            return

        if isinstance(value, str):
            self._append_signal(signals, source='body', field_path=field_path, value=value)

    def _append_signal(self, signals, source, field_path, value):
        if len(signals) >= self.max_signals:
            return

        pattern_names = [name for name, pattern in _SQL_PATTERNS if pattern.search(value)]
        if not pattern_names:
            return

        signals.append(
            {
                'source': source,
                'field': self._safe_field_path(field_path),
                'patterns': pattern_names,
            }
        )

    def _safe_field_path(self, field_path):
        normalized = field_path.lower()
        if any(marker in normalized for marker in _SENSITIVE_FIELD_MARKERS):
            return '[redacted]'
        return field_path
