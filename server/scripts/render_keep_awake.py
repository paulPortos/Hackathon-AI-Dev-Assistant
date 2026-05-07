#!/usr/bin/env python3
"""Ping the lightweight API health endpoint from an external scheduler."""

import argparse
import os
import socket
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_INTERVAL_SECONDS = 15
DEFAULT_TIMEOUT_SECONDS = 60


def env_int(name, default):
    value = os.getenv(name)
    if value in (None, ''):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def ping(url, timeout):
    request = Request(
        url,
        method='HEAD',
        headers={'User-Agent': 'render-keep-awake/1.0'},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, ''
    except HTTPError as exc:
        return exc.code, str(exc)
    except URLError as exc:
        return 0, str(exc.reason)
    except socket.timeout as exc:
        return 0, str(exc)
    except TimeoutError as exc:
        return 0, str(exc)
    except OSError as exc:
        return 0, str(exc)


def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}', flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description='Ping a Render-hosted API health endpoint.')
    parser.add_argument(
        '--url',
        default=os.getenv('KEEPALIVE_URL', ''),
        help='Full health endpoint URL, for example https://app.onrender.com/api/v1/health/.',
    )
    parser.add_argument(
        '--interval-seconds',
        type=int,
        default=env_int('KEEPALIVE_INTERVAL_SECONDS', DEFAULT_INTERVAL_SECONDS),
        help='Seconds between pings when running continuously.',
    )
    parser.add_argument(
        '--timeout-seconds',
        type=int,
        default=env_int('KEEPALIVE_TIMEOUT_SECONDS', DEFAULT_TIMEOUT_SECONDS),
        help='HTTP request timeout in seconds.',
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Send one ping and exit. Use this mode from cron-style schedulers.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.url:
        log('Missing --url or KEEPALIVE_URL.')
        return 2
    if args.interval_seconds < 15 and not args.once:
        log('Refusing to run continuously with interval below 15 seconds.')
        return 2

    while True:
        status_code, error = ping(args.url, args.timeout_seconds)
        if 200 <= status_code < 400:
            log(f'Ping ok: {status_code}')
            exit_code = 0
        else:
            detail = f': {error}' if error else ''
            log(f'Ping failed: {status_code or "no response"}{detail}')
            exit_code = 1

        if args.once:
            return exit_code
        time.sleep(args.interval_seconds)


if __name__ == '__main__':
    sys.exit(main())
