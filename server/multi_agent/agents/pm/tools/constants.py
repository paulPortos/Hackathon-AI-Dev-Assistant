PM_AGENT_NAME = 'PM Agent'

PRIORITY_SCORE = {
    'critical': 90,
    'high': 70,
    'medium': 45,
    'low': 20,
    'info': 10,
}

TASK_CATEGORY_KEYWORDS = {
    'vulnerability_fix': {'security', 'auth', 'vulnerability', 'cors', 'secret', 'token', 'xss', 'csrf', 'sql'},
    'feature': {'feature', 'enhancement', 'product', 'ui', 'ux'},
    'bug': {'bug', 'fix', 'broken', 'error', 'regression'},
    'refactor': {'refactor', 'cleanup', 'architecture', 'scalability', 'performance'},
    'research': {'research', 'investigate', 'spike', 'explore'},
}

ROLE_CATEGORY_KEYWORDS = {
    'vulnerability_fix': {'security', 'backend', 'devops', 'architect'},
    'feature': {'frontend', 'backend', 'fullstack', 'product', 'design'},
    'bug': {'backend', 'frontend', 'fullstack', 'qa'},
    'refactor': {'backend', 'frontend', 'fullstack', 'architect'},
    'research': {'architect', 'senior', 'lead', 'product', 'security'},
    'other': {'backend', 'frontend', 'fullstack'},
}
