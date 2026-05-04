import json
import logging
from datetime import datetime, timezone


_LOG_RECORD_ATTRIBUTES = {
    'args',
    'asctime',
    'created',
    'exc_info',
    'exc_text',
    'filename',
    'funcName',
    'levelname',
    'levelno',
    'lineno',
    'module',
    'msecs',
    'message',
    'msg',
    'name',
    'pathname',
    'process',
    'processName',
    'relativeCreated',
    'stack_info',
    'thread',
    'threadName',
}


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_ATTRIBUTES or key.startswith('_'):
                continue
            payload[key] = self._json_safe(value)

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        if record.stack_info:
            payload['stack_info'] = self.formatStack(record.stack_info)

        return json.dumps(payload, sort_keys=True)

    def _json_safe(self, value):
        if isinstance(value, dict):
            return {str(key): self._json_safe(child_value) for key, child_value in value.items()}

        if isinstance(value, (list, tuple)):
            return [self._json_safe(child_value) for child_value in value]

        try:
            json.dumps(value)
        except TypeError:
            return str(value)

        return value
