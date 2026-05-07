# Deployment Guide

This project deploys without Docker.

- Backend: Django + Channels in `server/`, deployed on Render.
- Frontend: Vite React app in `mocked-client/`, deployed on Vercel.
- Database: Neon Postgres or Render Postgres.
- WebSockets: Daphne on Render, with Redis recommended through `REDIS_URL`.

## 1. Choose A Postgres Database

Use only one of these options.

### Option A: Neon Postgres

1. Create a Neon project.
2. Open the Neon dashboard and click **Connect**.
3. Copy the Postgres connection string.
4. Use the pooled connection string if Neon offers one.
5. Make sure the URL includes `sslmode=require`.

Example:

```text
postgresql://user:password@ep-example.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Render backend env vars:

```text
DATABASE_URL=<your-neon-url-with-sslmode=require>
DATABASE_SSL_REQUIRE=True
DATABASE_CONN_MAX_AGE=600
```

When `DATABASE_URL` is set, do not set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, or `DB_PORT`.

### Option B: Render Postgres

1. In Render, click **New > PostgreSQL**.
2. Choose a name, region, and plan.
3. Put the database in the same region as your backend web service when possible.
4. After it is created, open the database page.
5. Click **Connect** or check the **Info** page.
6. Copy the **Internal Database URL**.

Use the internal URL for the Render backend service because it stays on Render's private network.

Render backend env vars:

```text
DATABASE_URL=<render-internal-database-url>
DATABASE_SSL_REQUIRE=False
DATABASE_CONN_MAX_AGE=600
```

If your app connects from outside Render, use the external URL instead. For the backend running on Render, prefer the internal URL.

## 2. Deploy The Backend On Render

In Render:

1. Click **New > Web Service**.
2. Connect this GitHub repo.
3. Select the branch you want to deploy.
4. Set **Runtime** to `Python 3`.
5. Set **Root Directory** to:

```text
server
```

Use these commands:

```text
Build Command:
pip install -r requirements.txt
```

```text
Pre-Deploy Command:
python manage.py migrate
```

```text
Start Command:
python -m daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

If your Render plan does not show a pre-deploy command field, use this start command instead:

```text
python manage.py migrate && python -m daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

Use Daphne instead of `python manage.py runserver` because this project uses Django Channels / WebSockets.

Set the Render health check path:

```text
/api/v1/health/
```

The health endpoint returns `204 No Content`, does not require auth, and does not touch the database.

## 3. Backend Environment Variables

Set these in the Render backend service.

```text
DJANGO_SECRET_KEY=<generated-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-backend-name>.onrender.com
DJANGO_TIME_ZONE=UTC
FRONTEND_URL=https://<your-vercel-app>.vercel.app
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app
DATABASE_URL=<neon-or-render-postgres-url>
DATABASE_SSL_REQUIRE=True-or-False-based-on-your-db
DATABASE_CONN_MAX_AGE=600
GITHUB_CLIENT_ID=<github-oauth-client-id>
GITHUB_CLIENT_SECRET=<github-oauth-client-secret>
GITHUB_CALLBACK_URL=https://<your-backend-name>.onrender.com/auth/github/callback/
GITHUB_TOKEN_ENCRYPTION_KEY=<fernet-key>
OLLAMA_API_KEY=<ollama-api-key>
OLLAMA_HOST=<your-ollama-host>
SR_DEV_AGENT_MODEL=gpt-oss:20b
PROJECT_MANAGER_AGENT_MODEL=gpt-oss:20b
JWT_ACCESS_TOKEN_MINUTES=60
JWT_REFRESH_TOKEN_DAYS=7
SECURITY_AUDIT_LOG_LEVEL=INFO
```

Recommended for production WebSockets:

```text
REDIS_URL=<your-redis-url>
```

Without `REDIS_URL`, Django Channels uses in-memory channels. That is fine locally, but it is not production-safe if Render restarts or you scale past one instance.

Optional agent tuning:

```text
OLLAMA_AGENT_MAX_ATTEMPTS=3
OLLAMA_AGENT_RETRY_DELAY_SECONDS=0.75
SR_DEV_TOOL_CALL_LIMIT=8
PROJECT_MANAGER_CONFIDENCE_THRESHOLD=75
```

Generate `GITHUB_TOKEN_ENCRYPTION_KEY` locally:

```bash
cd server
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a Django secret key locally:

```bash
cd server
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Private Key Secret File On Render

If you use a GitHub App private key, add it in Render as a **Secret File**.

Example filename:

```text
hackathon-codekada.2026-05-03.private-key.pem
```

Then set this backend env var:

```text
GITHUB_PRIVATE_KEY_PATH=/etc/secrets/hackathon-codekada.2026-05-03.private-key.pem
```

Render exposes secret files at:

```text
/etc/secrets/<filename>
```

Make sure the private key keeps its multiline PEM format:

```text
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

## 5. Configure GitHub OAuth

In your GitHub OAuth App settings:

```text
Homepage URL:
https://<your-vercel-app>.vercel.app
```

```text
Authorization callback URL:
https://<your-backend-name>.onrender.com/auth/github/callback/
```

This callback is not under `/api/v1/`. It is mounted at `/auth/github/callback/`.

## 6. Deploy The Frontend On Vercel

In Vercel:

1. Click **Add New > Project**.
2. Import this GitHub repo.
3. Set **Framework Preset** to `Vite`.
4. Set **Root Directory** to:

```text
mocked-client
```

Use these settings:

```text
Install Command:
npm install
```

```text
Build Command:
npm run build
```

```text
Output Directory:
dist
```

Set these Vercel environment variables:

```text
VITE_API_BASE_URL=https://<your-backend-name>.onrender.com
VITE_API_VERSION=v1
VITE_WS_BASE_URL=
```

Leave `VITE_WS_BASE_URL` blank unless your WebSocket server is on a different domain. The client automatically converts `https://` to `wss://`.

Vite reads `VITE_` variables during the build. After changing these in Vercel, redeploy the frontend.

This repo includes `mocked-client/vercel.json` so Vercel rewrites direct routes such as `/login`, `/home`, and `/projects/1` to `index.html`. This is required for React Router and for the GitHub callback redirect to `/login?access=...`.

## 7. Update Backend URLs After Vercel Deploys

After Vercel gives you the frontend URL, update the Render backend env vars:

```text
FRONTEND_URL=https://<your-vercel-app>.vercel.app
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app
```

Then redeploy the backend.

If you add a custom domain later, include both domains while switching:

```text
DJANGO_ALLOWED_HOSTS=<backend>.onrender.com,api.example.com
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app,https://app.example.com
FRONTEND_URL=https://app.example.com
```

## 8. Smoke Test

Backend health:

```bash
curl -I https://<your-backend-name>.onrender.com/api/v1/health/
```

Expected:

```text
HTTP/2 204
x-health-check: ok
```

Unauthenticated API routes should reject requests:

```bash
curl https://<your-backend-name>.onrender.com/api/v1/projects/
```

Expected: `401 Unauthorized`.

Open the frontend:

```text
https://<your-vercel-app>.vercel.app
```

Then test:

- GitHub login
- Import GitHub repository
- Project page
- Senior Dev session
- WebSocket chat

## 9. Keep Awake Ping

The repo includes a tiny pinger script:

```text
server/scripts/render_keep_awake.py
```

Run it from outside the same Render backend service:

```bash
python server/scripts/render_keep_awake.py \
  --url "https://<your-backend-name>.onrender.com/api/v1/health/"
```

It pings every 15 seconds by default.

You can also set the URL through an environment variable:

```bash
KEEPALIVE_URL="https://<your-backend-name>.onrender.com/api/v1/health/" \
python server/scripts/render_keep_awake.py
```

Do not run this inside the same sleeping web service. If the web service sleeps, the pinger sleeps too.

## 10. Common Problems

### `DisallowedHost`

Add the backend hostname to:

```text
DJANGO_ALLOWED_HOSTS
```

Example:

```text
DJANGO_ALLOWED_HOSTS=my-api.onrender.com
```

### Browser CORS Error

Add the Vercel frontend URL to:

```text
CORS_ALLOWED_ORIGINS
```

Example:

```text
CORS_ALLOWED_ORIGINS=https://my-client.vercel.app
```

### Frontend Calls Localhost

Set this in Vercel and redeploy:

```text
VITE_API_BASE_URL=https://<backend>.onrender.com
```

### GitHub Login Redirects To Localhost

Update both:

```text
GITHUB_CALLBACK_URL=https://<backend>.onrender.com/auth/github/callback/
FRONTEND_URL=https://<frontend>.vercel.app
```

Then update the GitHub OAuth App callback URL to match.

### Neon Database SSL Error

Make sure the Neon URL includes:

```text
?sslmode=require
```

Also set:

```text
DATABASE_SSL_REQUIRE=True
```

### Render Postgres Connection Error

For a Render backend connecting to Render Postgres, use the **Internal Database URL** and keep the backend service in the same region as the database.

```text
DATABASE_URL=<render-internal-database-url>
DATABASE_SSL_REQUIRE=False
```

### WebSocket Connects Locally But Fails In Production

Check:

```text
REDIS_URL=<redis-url>
VITE_API_BASE_URL=https://<backend>.onrender.com
```

The frontend converts the backend URL to `wss://` automatically.

## 11. Why No Docker Is Needed

Render and Vercel can build this project directly:

- Backend uses Render's Python runtime with `pip install -r requirements.txt`.
- Backend starts with Daphne using the Render-provided `$PORT`.
- Frontend uses Vercel's Vite build with `npm run build`.
- Database connection comes from `DATABASE_URL`.

Docker is only needed if you want full control over the operating system image or custom system packages. This project does not require Docker for a normal Render + Vercel deployment.

## References

- Render Django deploy docs: https://render.com/docs/deploy-django
- Render deploy commands: https://render.com/docs/deploys
- Render Postgres docs: https://render.com/docs/databases
- Neon connection strings and SSL guidance: https://neon.com/docs/connect/connection-errors
- Vercel Vite docs: https://vercel.com/docs/frameworks/frontend/vite
- Vercel environment variables: https://vercel.com/docs/projects/environment-variables
