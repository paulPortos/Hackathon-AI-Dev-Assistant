def user_description_get_agent_context(user_description):
    user = user_description.user
    return {
        'user': {
            'id': user.id,
            'github_id': user.github_id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'avatar_url': user.avatar_url,
        },
        'primary_role': user_description.primary_role,
        'experience_level': user_description.experience_level,
        'summary': user_description.summary,
        'skills': user_description.skills,
        'preferred_tasks': user_description.preferred_tasks,
        'avoided_tasks': user_description.avoided_tasks,
        'availability_notes': user_description.availability_notes,
        'agent_notes': user_description.agent_notes,
    }
