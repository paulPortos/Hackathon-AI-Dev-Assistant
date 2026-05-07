# Deploying To Render Without Docker

This project can deploy on Render with native runtimes. You do not need a Dockerfile.

The app has two deployable pieces:

- Django API / WebSocket backend: `server/`
- Vite React client: `mocked-client/`

The backend should use Neon Postgres for `DATABASE_URL`. For WebSockets in production, use Redis through `REDIS_URL`.

## 1. Prepare Neon Postgres

1. Create a Neon project.
2. Open the Neon project dashboard and click **Connect**.
3. Copy the Postgres connection string.
4. Use the pooled connection string if Neon offers one.
5. Make sure SSL is enabled. Your URL should include `sslmode=require`.

Example:

```text
postgresql://user:password@ep-example.us-east-2.aws.neon.tech/neondb?sslmode=require
```

You will paste this into Render as:

```text
DATABASE_URL=postgresql://...
DATABASE_SSL_REQUIRE=True
DATABASE_CONN_MAX_AGE=600
```

Do not set the separate `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, or `DB_PORT` values when `DATABASE_URL` is set.

## 2. Deploy The Backend Web Service

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
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

Use Daphne instead of `python manage.py runserver` because this project uses Django Channels / WebSockets.

Set the health check path:

```text
/api/v1/health/
```

The health endpoint returns `204 No Content`, does not require auth, and does not touch the database.

## 3. Backend Environment Variables

Set these in the Render backend service.

Required production values:

```text
DJANGO_SECRET_KEY=<generated-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-backend-name>.onrender.com
DJANGO_TIME_ZONE=UTC
FRONTEND_URL=https://<your-frontend-name>.onrender.com
CORS_ALLOWED_ORIGINS=https://<your-frontend-name>.onrender.com
DATABASE_URL=<your-neon-postgres-url-with-sslmode=require>
DATABASE_SSL_REQUIRE=True
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

If `REDIS_URL` is missing, Django Channels falls back to in-memory channels. That is okay for local development, but it is not production-safe if Render restarts or if you scale past one instance.

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

## 4. Configure GitHub OAuth

In your GitHub OAuth App settings:

```text
Homepage URL:
https://<your-frontend-name>.onrender.com
```

```text
Authorization callback URL:
https://<your-backend-name>.onrender.com/auth/github/callback/
```

This callback is not under `/api/v1/`. It is mounted at `/auth/github/callback/`.

## 5. Deploy The Frontend Static Site

In Render:

1. Click **New > Static Site**.
2. Connect the same repo.
3. Set **Root Directory** to:

```text
mocked-client
```

Use these settings:

```text
Build Command:
npm install && npm run build
```

```text
Publish Directory:
dist
```

Set this frontend environment variable:

```text
VITE_API_BASE_URL=https://<your-backend-name>.onrender.com
```

The client reads `VITE_API_BASE_URL` during the Vite build. If this is missing, it falls back to `http://localhost:8000`, which will not work in production.

For React Router, add a static site rewrite in Render:

```text
Source: /*
Destination: /index.html
Action: Rewrite
```

## 6. Update Backend URLs After Frontend Deploys

After the static site has its final Render URL, update these backend env vars:

```text
FRONTEND_URL=https://<your-frontend-name>.onrender.com
CORS_ALLOWED_ORIGINS=https://<your-frontend-name>.onrender.com
```

Then redeploy the backend.

If you use a custom domain later, add both the Render URL and custom domain while you are switching:

```text
DJANGO_ALLOWED_HOSTS=<backend>.onrender.com,api.example.com
CORS_ALLOWED_ORIGINS=https://<frontend>.onrender.com,https://app.example.com
FRONTEND_URL=https://app.example.com
```

## 7. Smoke Test

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
https://<your-frontend-name>.onrender.com
```

Then test:

- GitHub login
- Import GitHub repository
- Project page
- Senior Dev session
- WebSocket chat

## 8. Keep Awake Ping

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

## 9. Common Problems

### `DisallowedHost`

Add the backend hostname to:

```text
DJANGO_ALLOWED_HOSTS
```

Example:

```text
DJANGO_ALLOWED_HOSTS=my-api.onrender.com
```

### Browser CORS error

Add the frontend URL to:

```text
CORS_ALLOWED_ORIGINS
```

Example:

```text
CORS_ALLOWED_ORIGINS=https://my-client.onrender.com
```

### GitHub login redirects to localhost

Update both:

```text
GITHUB_CALLBACK_URL=https://<backend>.onrender.com/auth/github/callback/
FRONTEND_URL=https://<frontend>.onrender.com
```

Then update the GitHub OAuth App callback URL to match.

### Database SSL error

Make sure the Neon URL includes:

```text
?sslmode=require
```

Also set:

```text
DATABASE_SSL_REQUIRE=True
```

### WebSocket connects locally but fails on Render

Check:

```text
REDIS_URL=<redis-url>
VITE_API_BASE_URL=https://<backend>.onrender.com
```

The frontend converts `https://` to `wss://` for WebSockets automatically.

### Static frontend opens but refresh gives 404

Add the static site rewrite:

```text
/* -> /index.html
```

## 10. Why No Docker Is Needed

Render can build Python and Node apps directly:

- Backend uses Render's Python runtime with `pip install -r requirements.txt`.
- Frontend uses Render's static site build with `npm install && npm run build`.
- Start commands tell Render exactly how to run the backend process.

Docker is only needed if you want full control over the operating system image or custom system packages. This project does not require that for a normal Render deployment.

## References

- Render Django deploy docs: https://render.com/docs/deploy-django
- Render static site docs: https://render.com/docs/static-sites
- Render environment variables: https://render.com/docs/environment-variables
- Neon connection strings and SSL guidance: https://neon.com/docs/connect/connection-errors
