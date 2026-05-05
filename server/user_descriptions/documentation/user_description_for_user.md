# User Description for Specific User

## URL
`/api/<version>/user-descriptions/users/<user_id>/`

## Method
`GET`

## Query Parameters
None

## Request Body
None

## Response Body
```json
{
    "id": 1,
    "user_id": 123,
    "username": "targetuser",
    "name": "Target User",
    "email": "target@example.com",
    "primary_role": "Frontend Engineer",
    "experience_level": "Intermediate",
    "summary": "Focuses on UX...",
    "skills": [
        { "name": "JavaScript", "level": 4 }
    ],
    "preferred_tasks": ["Component design"],
    "avoided_tasks": ["DevOps"],
    "availability_notes": "Full-time",
    "agent_notes": "",
    "created_at": "2024-05-05T00:00:00Z",
    "updated_at": "2024-05-05T00:00:00Z"
}
```
