# agentic-crew

What would be the best way to have the minions work right within your laptop,
and work with like agents running elsewhere?

## Deployment options

### Local laptop / Cloudflare tunnel

The existing local deployment remains based on `docker-compose-tunneled.yml`.
It is intentionally independent of the Railway cloud deployment.

### Railway cloud deployment

A separate Railway deployment definition is provided in
[`docker-compose-railway.yml`](docker-compose-railway.yml). It deploys n8n,
PostgreSQL, Redis, Qdrant, and LiteLLM as separate Railway services. Ollama and
Langfuse are intentionally excluded from this cloud stack.

LiteLLM is built with [`Dockerfile.litellm`](Dockerfile.litellm), which copies
the cloud-only configuration from
[`config/litellm_config.railway.yaml`](config/litellm_config.railway.yaml)
into the image. This avoids relying on a repository-relative host bind mount
for a file that must exist inside the independently deployed Railway service.

See [`docs/RAILWAY_DEPLOYMENT.md`](docs/RAILWAY_DEPLOYMENT.md) for service
variables, Dockerfile selection, PostgreSQL database creation (`n8n` and
`litellm`), persistent volumes, private networking, custom-domain setup, and
smoke tests.

**Security:** Do not store API keys, passwords, or n8n encryption keys in this
repository. Configure them in the relevant Railway service Variables tab. Any
credentials previously committed should be rotated; deleting a value from the
latest file does not remove it from Git history.

## Repository layout

- `config/litellm_config.yaml`: local LiteLLM configuration (includes Ollama).
- `config/litellm_config.railway.yaml`: cloud-only LiteLLM configuration.
- `Dockerfile.litellm`: builds the Railway LiteLLM image and packages its YAML.
- `docker-compose-tunneled.yml`: existing laptop/tunnel deployment.
- `docker-compose-railway.yml`: Railway cloud deployment.
- `scripts/` and `notebooks/`: evaluation and utility scripts.

## Local startup

```bash
docker compose -f docker-compose-tunneled.yml up -d
```

If you also run the separate local Langfuse stack, start it using its existing
local instructions. Do not use the Railway Compose file to start the laptop
stack.

## Python evaluation environment

Create and activate a virtual environment, then install dependencies from
`requirements.txt`.

```bash
python -m venv ai_env
# Windows PowerShell: .\\ai_env\\Scripts\\Activate.ps1
# Linux/macOS: source ai_env/bin/activate
pip install -r requirements.txt
```

Never commit a populated `.env` file, database data directories, vector data,
or provider credentials.
