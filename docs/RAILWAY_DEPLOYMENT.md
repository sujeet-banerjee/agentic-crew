# Deploy the cloud stack to Railway

This deployment is deliberately separate from the laptop/tunnel stack. It does
not include Ollama or Langfuse and does not modify `docker-compose-tunneled.yml`
or `config/litellm_config.yaml`.

## Services and exposure

| Railway service | Purpose | Public access | Persistent path |
|---|---|---|---|
| `n8n` | Workflow UI and webhooks | Yes, custom domain, port 5678 | `/home/node/.n8n` |
| `postgres` | pgvector-capable relational store | No | `/var/lib/postgresql/data` |
| `redis` | Agent memory/cache service | No | `/data` |
| `qdrant` | Vector database | No | `/qdrant/storage` |
| `litellm` | LLM and embedding gateway | No | PostgreSQL database `litellm` |

PostgreSQL is one Railway service with two separate databases: `n8n` and
`litellm`. Qdrant is a separate Railway service and storage volume.

## 1. Create the Railway project and deploy the Compose file

1. Create a new Railway project (or use a separate environment dedicated to
   this cloud deployment).
2. Deploy this repository from GitHub and select
   `docker-compose-railway.yml` as the Compose file.
3. Confirm Railway creates five services named `n8n`, `postgres`, `redis`,
   `qdrant`, and `litellm`.
4. If Railway's Compose importer does not automatically attach persistent
   volumes, add one volume to each service at the exact mount path in the table
   above. Do this before relying on the deployment for data storage.
5. Do not enable public networking for `postgres`, `redis`, `qdrant`, or
   `litellm`. They communicate over Railway private networking.

Railway translates Compose services into separate Railway services. Compose
`depends_on` does not provide reliable startup ordering on Railway, so
services must tolerate a dependency taking time to become ready.

## 2. Set service variables

Set the following in each service's **Variables** tab. Use Railway-generated
reference variables where noted; do not paste secrets into GitHub.

### `postgres`

- `POSTGRES_DB=n8n`
- `POSTGRES_USER=agentic_crew`
- `POSTGRES_PASSWORD` = a newly generated, URL-safe random password

These initialization variables are applied only when PostgreSQL initializes an
empty data directory. Changing them later does not change existing credentials.

### `n8n`

- `N8N_ENCRYPTION_KEY` = a unique, stable random secret; keep it backed up
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` = reference the
  corresponding variables from the `postgres` service
- `GENERIC_TIMEZONE=Asia/Kolkata`
- `TZ=Asia/Kolkata`

The Compose file sets the internal database host to
`postgres.railway.internal` and the n8n schema to `public`.

### `redis`

- `REDIS_PASSWORD` = a unique random password

### `qdrant`

- `QDRANT_API_KEY` = a unique random API key

The Compose file maps it to Qdrant's `QDRANT__SERVICE__API_KEY`. Keep Qdrant
private; do not expose an API-key-protected Qdrant endpoint over plain HTTP.

### `litellm`

- `LITELLM_MASTER_KEY` = a unique random key beginning with `sk-`
- `LITELLM_DATABASE_URL` =
  `postgresql://agentic_crew:<POSTGRES_PASSWORD>@postgres.railway.internal:5432/litellm`
- `OPENAI_API_KEY` and/or `GROQ_API_KEY` / `HUGGINGFACE_API_KEY`, according
  to which configured models you intend to use

Use the actual password value in the URL. Generate a URL-safe password (for
example, hexadecimal output) so it does not require percent-encoding. Keep the
LiteLLM master key separate from the Qdrant API key and all database passwords.

## 3. Create the separate LiteLLM database

The PostgreSQL container creates only the initial `n8n` database. Once the
`postgres` service is healthy, connect using Railway's PostgreSQL
connection/Query interface or `railway connect postgres`, then run this SQL
once:

```sql
CREATE DATABASE litellm OWNER agentic_crew;
```

Verify both databases exist:

```sql
SELECT datname FROM pg_database WHERE datname IN ('n8n', 'litellm');
```

Then deploy/redeploy `litellm`. LiteLLM uses `litellm`; n8n uses `n8n`.
Neither application shares the other's database or tables.

## 4. Add the n8n custom domain

1. Open the Railway `n8n` service → **Settings** → **Networking** →
   **Custom Domain**.
2. Add `my.n8n.ai-maestro.in` and target port `5678`.
3. Railway will show the exact CNAME target and TXT verification record.
4. Add both records in Cloudflare exactly as Railway provides them. Initially
   use DNS-only (grey cloud) while validating the setup.
5. Do not alter the existing `n8n.ai-maestro.in` record used by the laptop
   deployment.

The n8n service is configured with HTTPS, `N8N_WEBHOOK_URL`,
`N8N_EDITOR_BASE_URL`, `N8N_PROXY_HOPS=1`, and secure cookies.

## 5. Validate the deployment

1. Wait until all five services report healthy/running; inspect logs for errors.
2. Open `https://my.n8n.ai-maestro.in`, create the owner account, and confirm
   the UI loads over HTTPS.
3. Create a Webhook-triggered workflow and verify its production URL externally.
4. Add a test credential, redeploy n8n, and verify the credential and workflow
   remain available. This checks the encryption key and volume.
5. Check LiteLLM's private health endpoint from another Railway service or
   Railway shell, then test a configured model using `LITELLM_MASTER_KEY`.
6. Verify Qdrant accepts its API key from an internal client and rejects a
   request without the key.
7. Restart/redeploy services and verify PostgreSQL, Redis, and Qdrant persist.

## Security and operational notes

- Keep the four supporting services private. Only n8n needs a public domain.
- Keep secrets in Railway Variables. `.env.railway.example` contains
  placeholders only and is a reference checklist, not a populated env file.
- Back up `N8N_ENCRYPTION_KEY` securely. Back up PostgreSQL and Qdrant
  independently; persistent volumes are not backups.
- Pin tested image versions after the first successful deployment. This Compose
  file currently uses floating image tags for initial setup.
- Verify LiteLLM model IDs and provider availability before relying on them.
- Redis uses password authentication and AOF persistence. n8n is not configured
  for queue mode; Redis is available for agent workflows that use it.
