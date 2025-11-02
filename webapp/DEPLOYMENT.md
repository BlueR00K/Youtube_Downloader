# Deployment with Docker

This repo contains a `docker-compose.yml` in `webapp/` that builds and runs the backend and frontend.

Quick start (requires Docker & Docker Compose):

```powershell
# from repository root
cd webapp
docker compose build
docker compose up
```

Services

- backend: built from `webapp/backend/Dockerfile`, exposes port 8000 inside container mapped to host 8000.
- frontend: built from `webapp/frontend/Dockerfile`, served by nginx on container port 80 and mapped to host 8080.

Environment variables

- ALLOWED_ORIGINS: comma-separated list of allowed origins for CORS (default: `*`).
- API_KEY: optional API key. If set, clients must send `X-API-KEY` header with this value to access protected endpoints.

Notes

- The docker setup is intended as a starting point. For production, add TLS termination, authentication, rate-limiting, persistent storage for large downloads, and background job processing for long-running downloads.
