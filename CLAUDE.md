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
| `db/database.py` | SQLAlchemy async engine + session factory; `init_db()` creates the DB and runs `metadata.create_all` on startup — no migration tool |
| `db/models.py` | ORM models: `User`, `Role`, `Event`, `Notification`, `Reminder` + M2M tables `user_roles`, `event_registrations`, `event_staff` |
| `schemas/classes.py` | Pydantic schemas: `UserCreate`, `UserUpdate`, `UserOut`, `LoginRequest`, `Token`, `RoleOut`, `NotificationOut`, `ReminderCreate`, `ReminderOut`, `EventCreate`, `EventOut` |
| `core/security.py` | `hash_password`, `verify_password` (bcrypt), `create_access_token`, `decode_token` (PyJWT / HS256, 24 h expiry, sub = user ID) |
| `core/dependencies.py` | `get_current_user` FastAPI dependency — reads `Authorization: Bearer <token>`, decodes the JWT, returns the `User` ORM object or raises 401 |
| `routes/__init__.py` | **Auto-discovery**: scans the `routes` package with `pkgutil` and registers every module that exports `router: APIRouter`. Adding a new file is enough — no manual wiring. All routes mount under `/api`. |
| `routes/user.py` | Full user system: login, register, me, CRUD, notifications, reminders — all wired to DB |
| `routes/events.py` | Event CRUD stubs — models exist, handlers not yet wired |
| `routes/apps.py` | Nextcloud proxy stubs (cloud, file viewer, calendar, contacts, notes) |
| `routes/nextcloud.py` | Functional Nextcloud admin routes via `nc-py-api` |

**Adding a protected route:** inject `current_user: User = Depends(get_current_user)` from `app.core.dependencies`. The dependency handles token validation and the 401 response automatically.

**DB session injection:** use `session: AsyncSession = Depends(get_session)` from `app.db.database`.

**Eager loading:** async SQLAlchemy does not support lazy loading. Always use `selectinload` or `joinedload` when a route needs relationships. The `_user_q()` helper in `routes/user.py` is the established pattern — returns a `select(User)` with all three relationships pre-loaded.

### Frontend (`front/`)

Next.js 16 App Router, React 19, TypeScript. Only root layout and a demo page exist.
- **shadcn/ui** (new-york style, Radix primitives) — scaffold with `pnpm dlx shadcn add <component>`
- **Material-UI v7** available alongside shadcn/ui
- **Tailwind CSS v4** with OKLch CSS custom properties for theming (`.dark` class toggles dark mode)
- Path alias `@/` maps to `front/` root (`tsconfig.json` + `components.json`)
- `cn()` utility in `front/lib/utils.ts` for conditional Tailwind classes

No API client, state management, or auth flow exists yet.

### Infrastructure

Docker Compose uses **profiles**: `dev` (source-mounted, hot-reload) and `prod` (production builds). Infrastructure services (`db`, `redis`, `nextcloud`) run in both profiles.

`back/.env` drives all secrets. `SECRET_KEY` must be set to a strong random value before any deployment — the default in `.env` is a placeholder.

## Key Conventions

- **New route files** need only to export `router = APIRouter()` — auto-discovered.
- **Schemas** in `back/app/schemas/classes.py`; **ORM models** in `back/app/db/models.py` — keep them separate.
- **Frontend components** go in `front/components/`.
- **Biome** (`biome.json` at root) is the formatter/linter for JS/TS.
