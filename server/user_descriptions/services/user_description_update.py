def user_description_update(*, user_description, data):
    allowed_fields = {
        'primary_role',
        'experience_level',
        'summary',
        'skills',
        'preferred_tasks',
        'avoided_tasks',
        'availability_notes',
        'agent_notes',
    }
    update_fields = []

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(user_description, field, value)
        update_fields.append(field)

    if update_fields:
        user_description.save(update_fields=[*update_fields, 'updated_at'])

    return user_description
