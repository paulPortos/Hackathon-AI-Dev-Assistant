def project_update_github_metadata(*, project, data):
    allowed_fields = {
        'github_repo_id',
        'github_full_name',
        'github_html_url',
        'github_clone_url',
        'github_default_branch',
        'github_visibility',
        'github_primary_language',
        'github_languages',
        'github_description',
        'github_is_private',
    }
    update_fields = []

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(project, field, value)
        update_fields.append(field)

    if update_fields:
        project.save(update_fields=[*update_fields, 'updated_at'])

    return project
