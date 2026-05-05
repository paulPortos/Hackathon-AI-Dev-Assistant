from users.services.github_token_expiry_from_seconds import github_token_expiry_from_seconds


def github_token_update_from_data(*, user, token_data):
    fields = {
        'access_token': token_data.get('access_token') or '',
        'github_access_token_expires_at': github_token_expiry_from_seconds(token_data.get('expires_in')),
    }

    if 'refresh_token' in token_data:
        fields['github_refresh_token'] = token_data.get('refresh_token') or ''
        fields['github_refresh_token_expires_at'] = github_token_expiry_from_seconds(token_data.get('refresh_token_expires_in'))

    for field, value in fields.items():
        setattr(user, field, value)

    user.save(update_fields=[*fields.keys(), 'updated_at'])
    return user
