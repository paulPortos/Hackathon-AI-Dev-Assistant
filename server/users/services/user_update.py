def user_update(*, user, **fields):
    allowed_fields = {'github_id', 'username', 'name', 'email', 'avatar_url', 'access_token', 'is_active', 'is_staff'}
    update_fields = []

    for field, value in fields.items():
        if field not in allowed_fields:
            continue
        setattr(user, field, value if value is not None else '')
        update_fields.append(field)

    if update_fields:
        user.save(update_fields=[*update_fields, 'updated_at'])

    return user
