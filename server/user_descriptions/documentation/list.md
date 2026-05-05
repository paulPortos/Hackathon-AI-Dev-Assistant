# User Description List

## URL
`/api/<version>/user-descriptions/`

## Method
`GET`

## Query Parameters
None (Supports standard Django Rest Framework pagination if configured)

## Request Body
None

## Response Body
```json
[
    {
        "id": 1,
        "user_id": 1,
        "username": "johndoe",
        "name": "John Doe",
        "email": "john@example.com",
        "primary_role": "Backend Engineer",
        "experience_level": "Senior",
        "summary": "Experienced Python developer...",
        "skills": [
            { "name": "Python", "level": 5 },
            { "name": "Django", "level": 4 }
        ],
        "preferred_tasks": ["API design", "Database optimization"],
        "avoided_tasks": ["CSS styling"],
        "availability_notes": "Available part-time",
        "agent_notes": "Likes clear instructions",
        "created_at": "2024-05-05T00:00:00Z",
        "updated_at": "2024-05-05T00:00:00Z"
    }
]
```
