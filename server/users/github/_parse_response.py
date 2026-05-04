from users.github.github_oauth_error import GitHubOAuthError


def _parse_response(response, message):
    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubOAuthError(message) from exc

    if response.status_code >= 400:
        detail = message
        if isinstance(data, dict):
            detail = data.get('error_description') or data.get('message') or message
        raise GitHubOAuthError(detail)

    return data
