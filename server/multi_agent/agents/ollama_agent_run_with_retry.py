import logging
import time

from django.conf import settings


_LOGGER = logging.getLogger('multi_agent.ollama')

_TRANSIENT_ERROR_MARKERS = (
    'status code: 500',
    'status code: 502',
    'status code: 503',
    'status code: 504',
    'Internal Server Error',
    'Bad Gateway',
    'Service Unavailable',
    'Gateway Timeout',
    'ReadTimeout',
    'ConnectTimeout',
    'ConnectionError',
    'RemoteProtocolError',
)


def _ollama_error_is_transient(exc):
    detail = str(exc)
    return any(marker in detail for marker in _TRANSIENT_ERROR_MARKERS)


def ollama_agent_run_with_retry(agent, prompt, *, agent_name):
    attempts = max(1, int(getattr(settings, 'OLLAMA_AGENT_MAX_ATTEMPTS', 3)))
    retry_delay_seconds = max(0.0, float(getattr(settings, 'OLLAMA_AGENT_RETRY_DELAY_SECONDS', 0.75)))
    last_exception = None

    for attempt in range(1, attempts + 1):
        try:
            return agent.run(prompt)
        except Exception as exc:
            last_exception = exc
            if attempt >= attempts or not _ollama_error_is_transient(exc):
                raise

            _LOGGER.warning(
                'ollama_agent_retry',
                extra={
                    'agent_name': agent_name,
                    'attempt': attempt,
                    'max_attempts': attempts,
                    'exception_class': exc.__class__.__name__,
                    'exception_detail': str(exc),
                },
            )
            if retry_delay_seconds:
                time.sleep(retry_delay_seconds * attempt)

    raise last_exception
