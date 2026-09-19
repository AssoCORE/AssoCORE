# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AssoCORE is a self-hosted association management platform (Epitech EIP). It is multi-layer: a FastAPI backend, a Next.js frontend, a Flutter mobile app, and an Astro documentation site, all orchestrated via Docker Compose (dev) or Kubernetes (prod).

## Development Commands

### Full stack (Docker)

One compose stack and one env file, both at the repo root. Run compose from the repo
root — it resolves `.env` relative to the directory you invoke it from.

```bash
# First time only
cp .env.example .env

# Run the app (hot-reload). --wait blocks until every service is healthy.
docker compose up --wait

# Production builds
docker compose --profile prod up --build

# Flutter APK — a one-shot build tool, deliberately outside dev/prod
docker compose --profile mobile up --build        # debug → ./build/mobile/
docker compose --profile mobile-prod up --build   # release
```

`.env` sets `COMPOSE_PROFILES=dev`, which is why a bare `docker compose up` runs the
app; an explicit `--profile` on the command line overrides it.

Required variables use `${VAR:?message}`, so a missing or incomplete `.env` makes
Compose refuse to start and name the variable, rather than starting containers with
blank credentials.

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
| `main.py` | FastAPI app init — async lifespan runs `init_db()` → `seed_all()` → redis ping, mounts `api_router`, adds CORS for localhost:3000, exposes `GET /health` |
| `db/database.py` | SQLAlchemy async engine + session factory; `init_db()` creates the DB and runs `metadata.create_all` on startup — no migration tool |
| `db/models.py` | ORM models: `User`, `Role`, `Event`, `Notification`, `Reminder`, `NextcloudAccount` + M2M tables `user_roles`, `event_registrations`, `event_staff` |
| `db/seed.py` | Startup seeding — default roles, a bootstrap admin from `ADMIN_*` env vars, and a `member` backfill for role-less users. Idempotent and safe to run on several replicas at once |
| `schemas/classes.py` | Pydantic schemas: `UserCreate`, `UserUpdate`, `UserOut`, `LoginRequest`, `Token`, `RefreshRequest`, `LogoutRequest`, `RoleOut`, `NotificationOut`, `ReminderCreate`, `ReminderOut`, `NcLink*`, `EventCreate`, `EventOut`. Validation lives here too — `PasswordStr` (8-50 chars, upper + lower + digit + one of `#?!@$%^&*-`), `EmailStr`, E.164 phone, event date ordering. A client that validates input itself must mirror these exactly or users get confusing 422s. |
| `core/security.py` | `hash_password`, `verify_password` (bcrypt), `create_access_token` / `create_refresh_token` / `create_token_pair`, `decode_token` (PyJWT / HS256; every token carries `typ` + `jti`) |
| `core/tokens.py` | `TokenStore` — redis-backed access-token blacklist and refresh-token rotation with reuse detection |
| `core/redis_client.py` | Process-wide async redis client (auth state on DB 1, separate from Nextcloud's DB 0) |
| `core/crypto.py` | Fernet `encrypt_secret` / `decrypt_secret` for Nextcloud app passwords stored in the DB |
| `core/roles.py` | Role name constants — `admin`, `staff`, `member` |
| `core/notifications.py` | `notify()` / `notify_many()` / `notify_role()` — the only writers of the `notifications` table |
| `core/dependencies.py` | `get_current_user` (validates the bearer token, checks the blacklist, eager-loads relations) and the `require_roles(*names)` / `require_admin` gates |
| `routes/__init__.py` | **Auto-discovery**: scans the `routes` package with `pkgutil` and registers every module that exports `router: APIRouter`. Adding a new file is enough — no manual wiring. Routers mount at the app root (`/user/...`, `/storage/...`) — there is **no** `/api` prefix. |
| `routes/user.py` | Full user system: login, refresh, logout, register, me, CRUD, notifications, reminders — all wired to DB |
| `routes/events.py` | Event CRUD stubs — models exist, handlers not yet wired |
| `routes/apps.py` | Nextcloud proxy stubs (cloud, file viewer, calendar, contacts, notes) |
| `routes/nextcloud.py` | Nextcloud admin routes via `nc-py-api` — **admin-gated at the router level** |
| `routes/nc_link.py` | Link a real Nextcloud account via Login Flow v2, storing an encrypted per-user app password |

**Adding a protected route:** inject `current_user: User = Depends(get_current_user)` from `app.core.dependencies`. The dependency handles token validation, revocation and the 401 response automatically. For admin-only routes use `Depends(require_admin)` (or `require_roles("staff", "admin")`); prefer putting it in the `APIRouter(dependencies=[...])` so new routes in that file cannot forget it.

**DB session injection:** use `session: AsyncSession = Depends(get_session)` from `app.db.database`.

**Eager loading:** async SQLAlchemy does not support lazy loading. Always use `selectinload` or `joinedload` when a route needs relationships. `_user_q()` in `routes/user.py` is the established pattern; `_deletable_user_q()` loads everything a cascading delete touches. Relationships read on every request (`User.nc_account`) instead declare `lazy="selectin"` on the model.

**Migrations:** there is no migration tool, and `metadata.create_all` only creates missing **tables** — it never adds a column to an existing one. Adding a field to a live model is a silent no-op against an existing database. Model new data as a new table (see `NextcloudAccount`), or introduce Alembic.

#### Auth flow

- `POST /user/login` → `{access_token, refresh_token, expires_in}`. The access token lasts 15 min; the refresh token 30 days.
- `POST /user/refresh` takes the refresh token (no `Authorization` header — the access token is expected to be expired) and rotates it. A rotated token inherits its predecessor's expiry, so refreshing never extends the absolute session lifetime.
- Replaying an already-used refresh token within `REFRESH_GRACE_SECONDS` (10 s) returns the same replacement pair, so concurrent browser tabs converge instead of fighting. Replaying it later is treated as theft: the whole token family is revoked and the user must log in again.
- `POST /user/logout` blacklists the current access token and, when given a refresh token, kills its family.
- Revocation state lives in redis. If redis is down, revocation checks are skipped (`AUTH_REDIS_STRICT=false`) but refresh and logout return 503 — they cannot be honoured without it.

#### Notifications

Nothing writes to `notifications` except `core/notifications.py`. Send one with
`notify(session, user_id, message, from_id=...)`, or `notify_role(...)` to reach everyone
holding a role. `from_id` records who caused it and is null for system-generated ones.

Call these **after** committing whatever triggered them: they manage their own
commit/rollback and swallow every `Exception`, so a notification that fails to insert
rolls back only itself and returns 0 rather than turning a successful action into a 500.
That only holds if the triggering work is already committed — notify last.

`POST /user/notification/` is the exception: creating one is the caller's whole intent
there, so it raises normally.

#### Nextcloud accounts

Every AssoCORE user has a matching Nextcloud account. By default its password is derived from `SECRET_KEY` + username, so a `SECRET_KEY` leak exposes every account. Users can instead link their real Nextcloud account through `POST /nextcloud/link/init` → browser approval → `GET /nextcloud/link/poll/{handle}`, which stores an encrypted per-user app password that `storage.py` prefers. Login re-checks the account at most once every `NC_PROBE_INTERVAL_HOURS` and re-provisions it if missing — but never resets the password of a linked account.

### Frontend (`front/`)

Next.js 16 App Router, React 19, TypeScript.
- **shadcn/ui** (new-york style, Radix primitives, Lucide icons) — scaffold with `pnpm dlx shadcn@latest add <component>`. If it fails with `Command failed with exit code 1: pnpm add -- cn`, that's pnpm's build-approval gate (`ERR_PNPM_IGNORED_BUILDS`) making the CLI's internal `pnpm add` exit non-zero even though the dependency install actually succeeded — run `pnpm approve-builds` once (already recorded in `front/pnpm-workspace.yaml`'s `allowBuilds`) and retry. Every component in `front/components/ui/` imports the local `cn()` from `@/lib/utils`; if the CLI ever emits an import from the standalone [`cn`](https://github.com/shadcn-ui/cn) package, rewrite it to match rather than adding the dependency.
- **Tailwind CSS v4** with OKLch CSS custom properties for theming (`.dark` class toggles dark mode)
- Path alias `@/` maps to `front/` root (`tsconfig.json` + `components.json`)
- `cn()` utility in `front/lib/utils.ts` for conditional Tailwind classes
- **Two linters, on purpose**: Biome (root `biome.json`) formats and lints; ESLint (`front/eslint.config.mjs`, run by `pnpm lint`) exists only for the Next-specific `core-web-vitals` rules Biome has no equivalent for. Don't add Prettier.
- `BACKEND_URL` is server-only (no `NEXT_PUBLIC_` prefix) and defaults to `http://localhost:8000` in `front/lib/backend.ts`; Compose overrides it per profile. There is deliberately no `front/.env.example` — the only value it could document is already the code default.
- `lucide-react` currently has no imports but is the configured `iconLibrary` in `components.json`, so `shadcn add` will emit Lucide imports. Don't remove it as "unused".

#### Auth (frontend)

The browser never calls FastAPI directly or holds a raw JWT — only same-origin Next.js
routes do, and the Next.js server calls the backend server-to-server (`front/lib/backend.ts`),
which sidesteps browser CORS entirely.

- `front/app/api/auth/{login,register,logout,refresh}/route.ts` are the only code that talks
  to the backend on the browser's behalf. `login`/`refresh` set httpOnly `access_token` /
  `refresh_token` cookies (both `path: "/"` — a narrower path would stop the browser attaching
  `refresh_token` to a plain page navigation, breaking the refresh design below).
- `front/proxy.ts` (Next.js 16 renamed `middleware.ts` → a file exporting `proxy`) runs before
  every protected-page request, decodes the access token's payload (no signature check — the
  backend re-validates that on every real call), and if it's expired calls `POST /user/refresh`
  itself, rewriting both the in-flight request's cookies and the response's before the Server
  Component renders — Server Components themselves cannot call `cookies().set()`. `/api/auth/refresh`
  is the reactive fallback for a client-side fetch that 401s mid-session, after the proxy already
  ran for that page load.
- `front/lib/auth/session.ts`'s `getCurrentUser()` (React `cache()`-wrapped) is the server-only
  `GET /user/me` getter used by pages/layouts; `front/lib/auth/roles.ts` mirrors the backend's
  `admin`/`staff`/`member` constants and `hasRole()`/`isAdmin()` checks.
- Route guards: `front/app/(protected)/layout.tsx` redirects to `/login` if unauthenticated;
  `(protected)/admin/layout.tsx` additionally requires the admin role, redirecting to
  `/unauthorized` otherwise — this is a UX gate only, the backend's own `require_admin` enforces
  it independently regardless of what the frontend does.
- `front/lib/auth/schemas.ts` mirrors the backend's password/phone/email regexes exactly so
  client-side zod errors match the server's 422s.

This pass is functional plumbing only (plain shadcn primitives, no design work) — the visual
design is tracked separately under issues #79/#80, which rebase onto this work.

### Infrastructure

Docker Compose uses **profiles**: `dev` (source-mounted, hot-reload, the default via
`COMPOSE_PROFILES` in `.env`), `prod` (production builds), and `mobile`/`mobile-prod`
for the Flutter APK builders. Infrastructure (`db`, `redis`, `nextcloud`) declares no
profile, so it runs in all of them. The APK builders are deliberately outside
`dev`/`prod`: they are one-shot build tools with no ready state, and in the dev profile
they ran a slow Flutter build on every `up` and broke `--wait`.

**There is one `.env`, at the repo root** (`.env.example` is the template). Compose reads
it twice over — to resolve the `${VAR}` substitutions inside `docker-compose.yml`, and as
the `env_file` injected into the `db`, `nextcloud` and `backend` containers. It has to sit
next to the compose file for the first of those, which is why compose must be run from the
repo root. This used to be split across a root `.env` and a `back/.env` that had to be kept
in sync by hand; they were merged because the drift silently produced blank credentials.

Required substitutions use `${VAR:?message}`, so a missing or incomplete `.env` aborts the
run naming the variable instead of starting MariaDB and Nextcloud with empty passwords.

Setting `DATABASE_URL` overrides the individual `MYSQL_*` vars that `db/database.py` otherwise composes the connection string from — worth knowing before adding one, since wiring it to the wrong credentials silently bypasses everything the `MYSQL_*` vars say. `SECRET_KEY` must be set to a strong random value before any deployment — the default is a placeholder. In production also set `NC_APP_PASSWORD_KEY` to an independent Fernet key (it otherwise derives from `SECRET_KEY`, which means one leak decrypts every stored Nextcloud app password) and `ADMIN_PASSWORD` (without it no admin account is seeded).

Redis backs auth revocation on DB 1. In Kubernetes the backend reads secrets from an optional `backend-secret`; see the comment in `k8s/09-backend/backend-deployment.yaml` for the `kubectl create secret` command.

The frontend's `BACKEND_URL` points at the backend service reachable from wherever Next.js itself runs — `http://backend:8000` / `http://backend_prod:8000` in the two `docker-compose.yml` profiles, `http://backend.assocore.svc.cluster.local:8000` in `k8s/10-frontend/frontend-config.yaml`. It's a plain server-only env var, not `NEXT_PUBLIC_*`.

## Key Conventions

- **New route files** need only to export `router = APIRouter()` — auto-discovered.
- **Schemas** in `back/app/schemas/classes.py`; **ORM models** in `back/app/db/models.py` — keep them separate.
- **Frontend components** go in `front/components/`.
- **Biome** (`biome.json` at root) is the formatter/linter for JS/TS — use it rather than Prettier.
