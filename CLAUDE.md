# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AssoCORE is a self-hosted association management platform (Epitech EIP). It is multi-layer: a FastAPI backend, a Next.js frontend, a Flutter mobile app, and an Astro documentation site, all orchestrated via Docker Compose (dev) or Kubernetes (prod).

## Development Commands

### Full stack (Docker)

```bash
# Start infrastructure + API in dev mode (hot-reload)
cd back && ./dev.sh

# Start everything (dev profile)
docker compose --profile dev up

# Start everything (prod profile)
docker compose --profile prod up --build
```

### Backend (FastAPI — `back/`)

```bash
# Run API directly (requires MariaDB running)
uv run dev   # uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
uv sync
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Nextcloud: http://localhost:8081

### Frontend (Next.js — `front/`)

```bash
pnpm dev      # dev server on :3000
pnpm build    # production build
pnpm lint     # ESLint
```

### Mobile (Flutter — `mobile/`)

```bash
flutter run
flutter build apk
```

### Documentation site (`docs/`)

```bash
pnpm dev    # Astro dev server
pnpm build  # static build
```

## Architecture

### Backend (`back/app/`)

| Path | Role |
|------|------|
| `main.py` | FastAPI app init — async lifespan calls `init_db()`, mounts `api_router`, adds CORS for localhost:3000 |
| `db/database.py` | SQLAlchemy async engine + session factory; `init_db()` creates the database and runs `metadata.create_all` on startup — no migration tool |
| `db/models.py` | SQLAlchemy ORM models: `User`, `Role`, `Event`, `Notification`, `Reminder`, plus M2M tables `user_roles`, `event_registrations`, `event_staff` |
| `schemas/classes.py` | Pydantic request/response models with validation (`PasswordStr`, `EmailStr`, E.164 phone, date ordering) |
| `routes/__init__.py` | **Auto-discovery**: scans the `routes` package with `pkgutil` and registers every module that exports a `router: APIRouter`. Adding a new route file is enough — no manual wiring needed. All routes mount under `/api`. |
| `routes/nextcloud.py` | Only functional route module — uses `nc-py-api` to proxy Nextcloud user/file operations |
| `routes/user.py`, `events.py`, `apps.py` | Stub implementations — all return `{"Response":"OK"}` |

**DB session injection:** use `Depends(get_session)` from `app.db` to get an `AsyncSession` in route handlers.

**Current state:** Route handlers are stubs with no DB queries. There is no auth/JWT, no password hashing, and no middleware beyond CORS.

### Frontend (`front/`)

Next.js 16 App Router with React 19 and TypeScript. Only the root layout and a demo page exist. UI layer is configured but empty:
- **shadcn/ui** (new-york style, Radix primitives) — scaffold components with `pnpm dlx shadcn add <component>`
- **Material-UI v7** — available alongside shadcn/ui
- **Tailwind CSS v4** with OKLch CSS custom properties for theming (light/dark via `.dark` class)
- Path alias `@/` maps to `front/` root (configured in `tsconfig.json` and `components.json`)

No API client, state management, or auth flow exists yet.

### Infrastructure

Docker Compose uses **profiles**: `dev` for development (source-mounted, hot-reload), `prod` for production builds. Infrastructure services (`db`, `redis`, `nextcloud`) run in both profiles.

The `back/.env` file drives all secrets (DB credentials, Nextcloud credentials). The `DATABASE_URL` env var overrides the individual `MYSQL_*` vars in `db/database.py`.

## Key Conventions

- **New backend route files** just need to export `router = APIRouter()` — they are auto-discovered.
- **Pydantic schemas** live in `back/app/schemas/classes.py`; ORM models in `back/app/db/models.py` — keep them separate.
- **Frontend components** go in `front/components/`; use `cn()` from `front/lib/utils.ts` for conditional Tailwind classes.
- **Biome** (`biome.json` at root) is the formatter/linter for JS/TS — run it instead of Prettier.
