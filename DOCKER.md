# Docker Setup Guide

This guide explains how to run the Life Organizer Backend with Docker and PostgreSQL.

## Quick Start

### Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Claude API key from [Anthropic Console](https://console.anthropic.com/settings/keys)

### 1. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example and edit
cp .env.example .env

# Set your Claude API key
CLAUDE_API_KEY=your_api_key_here
```

### 2. Start Everything

```bash
# Build and start all services (app + database)
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

That's it! The application will:
- Build the Docker image
- Start PostgreSQL database
- Wait for database to be ready
- Run Alembic migrations automatically
- Start the FastAPI server

### 3. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

## Docker Compose Commands

### Start Services

```bash
# Start in foreground (see logs)
docker-compose up

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

### Stop Services

```bash
# Stop services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes database data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# Specific service
docker-compose logs app
docker-compose logs db

# Last 100 lines
docker-compose logs --tail=100 -f
```

### Service Status

```bash
# Check status
docker-compose ps

# Check health
docker-compose ps
```

## Database Access

### Connect to PostgreSQL

```bash
# Using docker-compose
docker-compose exec db psql -U life_organizer -d life_organizer

# Or using psql from host (if installed)
psql postgresql://life_organizer:life_organizer_dev_password@localhost:5432/life_organizer
```

### Common PostgreSQL Commands

```sql
-- List schemas
\dn

-- List tables in budget schema
\dt budget.*

-- Describe budget.transactions table
\d budget.transactions

-- Query transactions
SELECT * FROM budget.transactions;

-- Exit psql
\q
```

## Migrations

Migrations run automatically on startup, but you can also run them manually:

```bash
# Run migrations manually
docker-compose exec app alembic upgrade head

# Check migration status
docker-compose exec app alembic current

# Rollback one migration
docker-compose exec app alembic downgrade -1

# View migration history
docker-compose exec app alembic history
```

## Development Workflow

### Hot Reload (Development Mode)

For development with hot reload, modify `docker-compose.yml`:

```yaml
app:
  # ... existing config ...
  volumes:
    - ./src:/app/src:ro  # Mount source code
  command: uvicorn life_organizer.main:app --host 0.0.0.0 --port 8000 --reload
```

Then restart:

```bash
docker-compose down
docker-compose up
```

### Run Tests Inside Container

```bash
# Run tests
docker-compose exec app pytest

# Run tests with coverage
docker-compose exec app pytest --cov=life_organizer

# Run specific test
docker-compose exec app pytest tests/test_main.py
```

### Shell Access

```bash
# Python shell
docker-compose exec app python

# Bash shell
docker-compose exec app bash

# Database shell
docker-compose exec db psql -U life_organizer
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if database is healthy
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Application Won't Start

```bash
# View application logs
docker-compose logs app

# Check if migrations are failing
docker-compose exec app alembic current

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Port Already in Use

If port 8000 or 5432 is already in use:

```yaml
# In docker-compose.yml, change the port mapping
ports:
  - "8001:8000"  # Use 8001 on host instead
```

### Reset Everything

```bash
# Stop and remove everything (including data)
docker-compose down -v

# Remove dangling images
docker system prune -f

# Rebuild from scratch
docker-compose up --build
```

## Environment Variables

All environment variables can be set in:

1. `.env` file (recommended for local development)
2. `docker-compose.yml` (for defaults)
3. Command line: `CLAUDE_API_KEY=xxx docker-compose up`

### Required Variables

- `CLAUDE_API_KEY` - Your Anthropic Claude API key

### Optional Variables

- `DEBUG` - Enable debug mode (default: `true`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `CORS_ORIGINS` - Allowed CORS origins
- `DATABASE_URL` - Database connection (auto-configured in Docker)

## Production Deployment

For production deployment, see the main README.md for Railway deployment instructions.

Docker Compose is recommended for:
- Local development
- Testing
- Self-hosted deployments

## Architecture

```
┌─────────────────────────────────────────┐
│  Docker Compose Network                 │
│                                         │
│  ┌────────────────┐  ┌───────────────┐ │
│  │  PostgreSQL    │  │  FastAPI App  │ │
│  │  (port 5432)   │◄─┤  (port 8000)  │ │
│  │                │  │               │ │
│  │  - Database    │  │  - Migrations │ │
│  │  - Persistence │  │  - API        │ │
│  └────────────────┘  └───────────────┘ │
│                                         │
└─────────────────────────────────────────┘
         │                    │
         │                    │
    localhost:5432       localhost:8000
```

## Next Steps

1. Access API docs: http://localhost:8000/api/v1/docs
2. Try the classifier endpoint
3. Check database: `docker-compose exec db psql -U life_organizer`
4. View logs: `docker-compose logs -f`

For more information, see the main README.md.
