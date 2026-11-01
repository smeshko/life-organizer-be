# Deployment Guide - life-organizer-be

## Deployment Options

### 1. Production

Production runs on the maintainer's own machine behind Cloudflare at `https://org.ivot.dev`
(health: `https://org.ivot.dev/health`).

### 2. Docker Compose (Local/Self-Hosted)

Docker Compose setup, service management, logs, database access, migrations, hot reload,
running tests in a container, shell access and troubleshooting are covered in
[docker.md](docker.md).

## Environment Configuration

### Required Variables
- `API_KEY` - key clients send to authenticate requests
- `CLAUDE_API_KEY` - Anthropic Claude API key

### Optional Variables
- `DEBUG` - Enable debug mode (default: `false`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `CORS_ORIGINS` - Allowed CORS origins
- `DATABASE_URL` - Database connection (auto-configured in Docker)

### Configuration Sources (priority order)
1. Environment variables
2. `.env` file
3. `docker-compose.yml` defaults

## Health Checks

The app includes health checks:

```bash
# Check service status
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health
```

## Configuration Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Multi-container orchestration |
| `.env.example` | Environment template |
| `alembic.ini` | Migration configuration |
