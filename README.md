# Life Organizer Backend

A budget capture and query API for the Life Organizer iOS app. It classifies free-text and screenshot input with
Claude, stores transactions, budget plans and feedback in PostgreSQL, and serves the app behind API-key auth.

Production runs at `https://org.ivot.dev`.

## Quick start

```bash
make dev                # install dependencies and pre-commit hooks
cp .env.example .env    # then fill in the keys
make db-setup           # create the database schema
make run                # serve on http://localhost:8000
```

With `DEBUG=true` the interactive docs are at `http://localhost:8000/api/v1/docs`.

## Checks

```bash
scripts/gate.sh          # ruff, mypy and the unit tests
make test-integration    # calls the real Anthropic API; needs ANTHROPIC_API_KEY
```

## More

- [AGENTS.md](AGENTS.md): conventions, module map and doc map
- [openapi.yaml](openapi.yaml): the API contract
- [docs/development/setup.md](docs/development/setup.md)
- [docs/development/docker.md](docs/development/docker.md)
- [docs/development/deployment-guide.md](docs/development/deployment-guide.md)
