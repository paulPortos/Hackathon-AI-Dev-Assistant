# Visor Client (React)

This folder provides the Visor frontend for project review, repository assistance, and team workflow checks.

## Quick start
1. cd mocked-client
2. npm install
3. npm run dev

## Env
Copy `.env.example` to `.env.local` for local development:

```bash
cp .env.example .env.local
```

Available variables:

- `VITE_API_BASE_URL` (default: `http://localhost:8000`)
- `VITE_API_VERSION` (default: `v1`)
- `VITE_WS_BASE_URL` (optional; defaults to `ws://` or `wss://` derived from `VITE_API_BASE_URL`)

Local example:

```text
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
VITE_WS_BASE_URL=
```

Vercel example:

```text
VITE_API_BASE_URL=https://your-backend.onrender.com
VITE_API_VERSION=v1
VITE_WS_BASE_URL=
```

Vite reads these values at build time. After changing them in Vercel, redeploy the project.

## GitHub OAuth flow (backend is the source of truth)
1. Start at /auth/github/login/ (backend, not /api).
2. GitHub redirects to /auth/github/callback/.
3. The backend redirects to `/login?access=...&refresh=...`.
4. The Login page stores the tokens and redirects to `/home`.

## Auth header
Authorization: Bearer <access>

## Token refresh
POST /api/v1/auth/tokens/refresh/ { "refresh": "..." }

## Endpoints by page
Login
- GET /auth/github/login/
- GET /auth/github/callback/

Home
- GET /api/v1/projects/
- POST /api/v1/projects/import-from-github/ { repository }

Projects
- GET /api/v1/projects/github/repositories/

Profile
- GET /api/v1/users/me/
- GET /api/v1/user-descriptions/current-user/
- PATCH /api/v1/user-descriptions/current-user/

Project
- GET /api/v1/projects/<id>/
- GET /api/v1/projects/<id>/tasks/
- GET /api/v1/projects/<id>/vulnerabilities/
- GET /api/v1/projects/<id>/members/
- POST /api/v1/projects/<id>/members/ { user_id, display_role, roles }
- PATCH /api/v1/projects/<id>/members/<member_id>/
- DELETE /api/v1/projects/<id>/members/<member_id>/
- GET /api/v1/projects/<id>/meeting-settings/
- PUT or PATCH /api/v1/projects/<id>/meeting-settings/
- GET /api/v1/projects/<id>/repository/branches/
- GET /api/v1/users/search/?q=
- GET /api/v1/users/<id>/
- GET /api/v1/user-descriptions/users/<id>/

Senior Dev
- GET /api/v1/agents/sr-dev/sessions/
- POST /api/v1/agents/sr-dev/sessions/ { project_id, commit_sha, branch_name }
- GET /api/v1/agents/sr-dev/sessions/<id>/
- GET /api/v1/agents/sr-dev/sessions/<id>/messages/
- POST /api/v1/agents/sr-dev/sessions/<id>/messages/ { input_type, text | choice | choice_payload | audio }

## Notes for integration
- The server uses JWT (access + refresh). Store both and attach the access token to every API request.
- List endpoints may be paginated. The UI normalizes data.results when present.
