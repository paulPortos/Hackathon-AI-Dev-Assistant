def user_update(*, user, **fields):
    allowed_fields = {
        'github_id',
        'username',
        'name',
        'email',
        'avatar_url',
        'access_token',
        'github_refresh_token',
        'github_access_token_expires_at',
        'github_refresh_token_expires_at',
        'is_active',
        'is_staff',
    }
    update_fields = []

    for field, value in fields.items():
        if field not in allowed_fields:
            continue
        setattr(user, field, value)
        update_fields.append(field)

    if update_fields:
        user.save(update_fields=[*update_fields, 'updated_at'])

    return user
