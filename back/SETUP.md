# AssoCORE Backend Setup Complete ✓

## What's Been Set Up

Your FastAPI backend is ready with:
- ✅ **uv** for fast Python package management
- ✅ **FastAPI** with async SQLAlchemy
- ✅ **Nextcloud integration** (nc-py-api)
- ✅ **Docker Compose** setup (MariaDB + Redis + Nextcloud + API)
- ✅ **Nix integration** (uses Python from flake.nix)

## Quick Start

### Development (Standalone API)

```bash
cd back
nix develop  # or use direnv
./dev.sh
```

API runs at: http://localhost:8000
Docs at: http://localhost:8000/docs

### Full Stack (with Nextcloud)

```bash
cd back
docker-compose up
```

- API: http://localhost:8000
- Nextcloud: http://localhost:8080
- Docs: http://localhost:8000/docs

## Project Structure

```
back/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── routes/
│   │   ├── __init__.py      # Router aggregation
│   │   └── nextcloud.py     # Nextcloud endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      # SQLAlchemy async setup
│   └── schemas/             # Pydantic models
├── pyproject.toml           # uv dependencies
├── uv.lock                  # Locked dependencies
├── docker-compose.yml       # Full stack
├── Dockerfile               # API container
├── .env                     # Environment variables
└── dev.sh                   # Quick dev script
```

## API Endpoints (from POC)

### Nextcloud Integration
- `GET /api/nextcloud/users` - List all users
- `POST /api/nextcloud/users` - Create user
- `GET /api/nextcloud/files/{user_id}` - List user files

### Health
- `GET /` - API status

## Environment Variables

Edit `back/.env`:
- Database credentials
- Nextcloud URL and admin credentials
- Connection settings

## Adding New Routes

1. Create route file in `app/routes/`
2. Import and include in `app/routes/__init__.py`
3. Routes auto-register with `/api` prefix

## Adding Dependencies

```bash
cd back
uv add <package-name>
```

## Integration with Nix

Your `flake.nix` already provides:
- Python 3.11
- uv package manager
- black + isort (pre-commit hooks)

Everything works seamlessly!
