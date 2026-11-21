# Deploy the cloud stack to Railway

This deployment is deliberately separate from the laptop/tunnel stack. It does
not include Ollama or Langfuse and does not modify `docker-compose-tunneled.yml`
or the local LiteLLM configuration.

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

## 1. Create/import the Railway project

1. Create an empty Railway project.
2. Import `docker-compose-railway.yml` into the project canvas.
3. Confirm Railway creates five services named `n8n`, `postgres`, `redis`,
   `qdrant`, and `litellm`.
4. Railway translates Compose services into separate Railway services; it does
   not run Docker Compose as the production orchestrator.
5. If Railway's importer does not automatically attach persistent volumes, add
   one volume to each service at the exact persistent path in the table above.
6. Keep `postgres`, `redis`, `qdrant`, and `litellm` private. Only n8n
   needs public networking.

Railway does not guarantee Compose `depends_on` startup ordering. Services must
tolerate dependencies becoming ready after the application starts.

## 2. LiteLLM image build and configuration file

LiteLLM needs a YAML configuration file at runtime. A repository-relative
Compose bind mount such as
`./config/litellm_config.railway.yaml:/app/config.yaml:ro` is not used here:
Railway services are independent deployments, not containers sharing a
repository checkout as a host filesystem.

Instead, the Compose definition uses:

```yaml
litellm:
  build:
    context: .
    dockerfile: Dockerfile.litellm
```

The root-level `Dockerfile.litellm` builds from the official LiteLLM image and
copies `config/litellm_config.railway.yaml` into the image at
`/app/config.yaml`. The file remains independently maintained in GitHub; it
is simply packaged into the LiteLLM image at build time. No bind mount is
required.

### If the LiteLLM service was already imported as an image service

Changing the Compose file in GitHub does not necessarily rewrite the existing
Railway service's source/build settings. For the existing `litellm` service:

1. Open LiteLLM → **Settings → Source**.
2. Change its source to the GitHub repository
   `sujeet-banerjee/agentic-crew`.
3. Select branch `enhance/saasify`.
4. Keep the Root Directory at the repository root (blank/default).
5. Under Build settings, set the Dockerfile path to
   `Dockerfile.litellm`. If using the platform variable instead, add
   `RAILWAY_DOCKERFILE_PATH=Dockerfile.litellm` to the LiteLLM service.
6. Remove the old imported bind-mount entry
   `./config/litellm_config.railway.yaml:/app/config.yaml:ro`. Do not delete
   the service or any unrelated persistent volume.
7. Leave custom Build Command and Start Command empty. The Dockerfile supplies
   the startup arguments.
8. Check the next build logs for evidence that Railway selected the custom
   Dockerfile and copied the YAML file.

Railway documents the `build:` to GitHub/Dockerfile mapping in its Compose
guide and the `RAILWAY_DOCKERFILE_PATH` setting in its Dockerfile guide.

## 3. Set service variables

Set variables in the corresponding Railway service's **Variables** tab.
Compose expressions such as `${VAR:?message}` may be imported as literal
strings; replace those placeholders with actual values or Railway reference
variables. Do not leave literal `${...}` expressions in deployed variables.

### `postgres`

- `POSTGRES_DB=n8n`
- `POSTGRES_USER=agentic_crew`
- `POSTGRES_PASSWORD` = a newly generated, URL-safe random password

Important: the official PostgreSQL image uses these initialization variables
only when the data directory is empty. If the attached PostgreSQL volume has
already been initialized, changing `POSTGRES_USER` or `POSTGRES_PASSWORD`
in Railway Variables does not change the database role/password inside the
existing database. Keep the credentials that were used during first
initialization, or deliberately alter the PostgreSQL role from SQL before
changing the application references.

### `n8n`

- `N8N_ENCRYPTION_KEY` = a unique, stable random secret; back it up securely
- `GENERIC_TIMEZONE=Asia/Kolkata`
- `TZ=Asia/Kolkata`
- `DB_POSTGRESDB_DATABASE=n8n`
- `DB_POSTGRESDB_USER=agentic_crew`
- `DB_POSTGRESDB_PASSWORD=${{postgres.POSTGRES_PASSWORD}}`

The Compose file sets the internal database host to
`postgres.railway.internal`, port `5432`, and schema `public`. If those
settings were imported as unresolved expressions, set them explicitly in
Railway Variables. Do not generate a new encryption key after n8n has stored
credentials; changing it can make existing encrypted credentials unreadable.

### `redis`

- `REDIS_PASSWORD` = a unique random password

Redis is started with password authentication and AOF persistence.

### `qdrant`

- `QDRANT_API_KEY` = a unique random API key

The Compose file maps it to `QDRANT__SERVICE__API_KEY`. Keep Qdrant private.

### `litellm`

- `LITELLM_MASTER_KEY` = a unique random key beginning with `sk-`
- `LITELLM_DATABASE_URL` =
  `postgresql://agentic_crew:${{postgres.POSTGRES_PASSWORD}}@postgres.railway.internal:5432/litellm`
- `OPENAI_API_KEY`, `GROQ_API_KEY`, and/or `HUGGINGFACE_API_KEY`, according
  to which configured models you intend to use
- `RAILWAY_DOCKERFILE_PATH=Dockerfile.litellm` only if the Build settings have
  not already selected that Dockerfile

Use a URL-safe PostgreSQL password (for example, hexadecimal output) so it
does not need URL percent-encoding. The LiteLLM master key must be separate
from the Qdrant API key and all database passwords.

### Generating secrets on Windows PowerShell

PowerShell on Windows 11 can generate a cryptographically random 32-byte
hexadecimal secret with:

```powershell
[Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Use a fresh value for each independent secret. For the LiteLLM master key,
prefix a fresh generated value with `sk-`. Do not paste secrets into GitHub,
screenshots, or chat.

## 4. Create the separate LiteLLM database

The PostgreSQL container creates only the initial `n8n` database. Once the
`postgres` service is healthy and its user/password are confirmed, connect
using Railway's PostgreSQL Query interface or Railway CLI and run:

```sql
CREATE DATABASE litellm OWNER agentic_crew;
```

If the database already exists, do not run the create statement again. Verify
both databases:

```sql
SELECT datname FROM pg_database WHERE datname IN ('n8n', 'litellm');
```

Then deploy/redeploy LiteLLM. LiteLLM uses `litellm`; n8n uses `n8n`.
Neither application shares the other's database or tables.

## 5. Add the n8n custom domain

1. Open the Railway n8n service → **Settings → Networking → Custom Domain**.
2. Add `my.n8n.ai-maestro.in` and target port `5678`.
3. Railway will show the exact CNAME target and TXT verification record.
4. Add both records in Cloudflare exactly as Railway provides them. Initially
   use DNS-only (grey cloud) while validating the setup.
5. Do not alter the existing `n8n.ai-maestro.in` record used by the laptop
   deployment.

The n8n service is configured with HTTPS, `N8N_WEBHOOK_URL`,
`N8N_EDITOR_BASE_URL`, `N8N_PROXY_HOPS=1`, and secure cookies.

## 6. Validate the deployment

1. Wait until all five services report healthy/running; inspect logs for errors.
2. Open `https://my.n8n.ai-maestro.in`, create the owner account, and confirm
   the UI loads over HTTPS.
3. Create a webhook-triggered workflow and verify its production URL externally.
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
  placeholders only; it is a checklist, not a populated env file.
- Back up `N8N_ENCRYPTION_KEY` securely. Persistent volumes are not backups.
- Pin tested image versions after the first successful deployment. This
  Compose file currently uses floating image tags for initial setup.
- Verify LiteLLM model IDs and provider availability before relying on them.
- Redis is available for agent workflows; n8n is not configured for queue mode.
