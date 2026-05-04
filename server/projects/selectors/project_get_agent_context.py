from user_descriptions.models import UserDescription
from user_descriptions.selectors import user_description_get_agent_context


def project_get_agent_context(project):
    members = list(project.members.select_related('user').all())
    descriptions = UserDescription.objects.select_related('user').filter(user_id__in=[member.user_id for member in members])
    descriptions_by_user_id = {description.user_id: description for description in descriptions}

    return {
        'project': {
            'id': project.id,
            'github_repo_id': project.github_repo_id,
            'github_full_name': project.github_full_name,
            'github_html_url': project.github_html_url,
            'github_default_branch': project.github_default_branch,
            'github_visibility': project.github_visibility,
            'github_primary_language': project.github_primary_language,
            'github_languages': project.github_languages,
            'github_description': project.github_description,
            'overview': project.overview,
            'goals': project.goals,
            'tech_stack': project.tech_stack,
            'business_context': project.business_context,
            'agent_notes': project.agent_notes,
        },
        'members': [
            {
                'id': member.id,
                'display_role': member.display_role,
                'roles': member.roles,
                'user_description': user_description_get_agent_context(descriptions_by_user_id[member.user_id])
                if member.user_id in descriptions_by_user_id
                else None,
            }
            for member in members
        ],
    }
