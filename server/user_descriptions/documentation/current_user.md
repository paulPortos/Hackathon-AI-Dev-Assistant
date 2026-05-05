# Current User Description Detail

## URL
`/api/<version>/user-descriptions/current-user/`

## Method
`GET`

### Query Parameters
None

### Request Body
None

### Response Body
```json
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
```

## Method
`PATCH`

### Query Parameters
None

### Request Body
Partial fields of the User Description object:
```json
{
    "primary_role": "Fullstack Engineer",
    "skills": [
        { "name": "Python", "level": 5 },
        { "name": "React", "level": 3 }
    ]
}
```

### Response Body
```json
{
    "id": 1,
    "user_id": 1,
    "username": "johndoe",
    "name": "John Doe",
    "email": "john@example.com",
    "primary_role": "Fullstack Engineer",
    "experience_level": "Senior",
    "summary": "Experienced Python developer...",
    "skills": [
        { "name": "Python", "level": 5 },
        { "name": "React", "level": 3 }
    ],
    "preferred_tasks": ["API design", "Database optimization"],
    "avoided_tasks": ["CSS styling"],
    "availability_notes": "Available part-time",
    "agent_notes": "Likes clear instructions",
    "created_at": "2024-05-05T00:00:00Z",
    "updated_at": "2024-05-05T00:00:00Z"
}
```
