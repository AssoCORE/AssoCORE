# AssoCORE Backend

FastAPI backend with Nextcloud integration.

## Stack

- **Framework**: FastAPI
- **Database**: MariaDB + SQLAlchemy (async)
- **Integration**: Nextcloud (nc-py-api)
- **Package Manager**: uv

## Development

### Full Stack (Recommended)

```bash
cd back
./setup.sh
```

- API: http://localhost:8000
- Nextcloud: http://localhost:8080
- Docs: http://localhost:8000/docs

### API Only (Dev Mode)

```bash
cd back
./dev.sh
```

⚠️ **Note**: Dev mode starts only the FastAPI server. Database and Nextcloud endpoints will fail without Docker services. Use for API development without external dependencies.

### Shutdown

```bash
cd back
./shutdown.sh
```

## Project Structure

```
back/
├── app/
│   ├── main.py          # FastAPI app
│   ├── routes/          # API endpoints
│   │   └── nextcloud.py # Nextcloud integration
│   ├── db/              # Database
│   │   └── database.py  # SQLAlchemy setup
│   └── schemas/         # Pydantic models
├── pyproject.toml       # uv dependencies
└── docker-compose.yml   # Full stack
```

## API Endpoints

- `GET /` - Health check
- `GET /docs` - Swagger UI
- `GET /nextcloud/users` - List Nextcloud users
- `POST /nextcloud/users` - Create Nextcloud user
- `GET /nextcloud/files/{user_id}` - List user files
