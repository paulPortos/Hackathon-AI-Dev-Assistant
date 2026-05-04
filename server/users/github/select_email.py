def select_email(*, github_user, github_emails):
    if github_user.get('email'):
        return github_user['email']

    for email in github_emails:
        if email.get('primary') and email.get('verified') and email.get('email'):
            return email['email']

    return ''
