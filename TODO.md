# TODO

Immediate and near-term work, by component.

---

## Backend

### Auth & Users (F1)

- [x] JWT login endpoint (`POST /user/login`) with bcrypt password verification
- [x] User register, read, update, delete wired to DB
- [x] `GET/PUT/DELETE /user/me` for the authenticated user
- [x] Notification routes (list, get, read/unread, delete) scoped to current user
- [x] Reminder routes (create, list, get, delete) scoped to current user
- [x] `core/security.py` — bcrypt + PyJWT helpers
- [x] `core/dependencies.py` — `get_current_user` FastAPI dependency
- [x] `core/roles.py` + `db/seed.py` — default roles seeded, admin bootstrapped from `ADMIN_*` env vars, `member` backfilled onto role-less users
- [x] Enforce RBAC: `require_roles` / `require_admin` dependencies; `routes/nextcloud.py` gated at the router level and `DELETE /user/{id}` is admin-only
- [x] Refresh tokens — 15 min access + 30 day refresh, rotation with reuse detection, `POST /user/logout` revocation (redis-backed)
- [ ] `GET /user/` should be admin-only, or return a reduced payload for non-admins
- [ ] Rate limiting on `POST /user/login` to prevent brute-force
- [ ] Change `SECRET_KEY` placeholder in `.env` before any deployment (and set an independent `NC_APP_PASSWORD_KEY`)
- [ ] `POST /user/logout/all` to end every session for a user at once

### Events (F3)

- [ ] Wire `back/app/routes/events.py` to the DB — models and schemas defined, all handlers return stubs
- [ ] `POST /event/{id}/register` and `DELETE /event/{id}/register` for member self-registration
- [ ] `POST /event/{id}/checkin` for attendance tracking (F4)

### Cloud / Apps (F2)

- [x] Provision Nextcloud user on `POST /user/` (deterministic password via HMAC — no NC password stored in DB)
- [x] `GET/DELETE /storage/` — list and delete files/folders
- [x] `GET /storage/info` — file metadata
- [x] `GET /storage/search` — search by name
- [x] `POST /storage/upload` — upload file (multipart)
- [x] `GET /storage/download` — download file (binary stream)
- [x] `POST /storage/folder` — create folder (with `makedirs`)
- [x] `POST /storage/move` and `POST /storage/copy`
- [x] `POST /storage/favourite` and `GET /storage/favourites`
- [x] `apps.py` — returns Nextcloud embedded-app URLs (cloud, viewer, calendar, contacts, notes)
- [x] `nextcloud.py` — admin user management (create, delete, enable, disable) + admin file browse
- [x] Link a real Nextcloud account via Login Flow v2 (`routes/nc_link.py`) — stores a Fernet-encrypted per-user app password that `storage.py` prefers over the derived one
- [x] Re-check and re-provision the Nextcloud account at login, throttled by `NC_PROBE_INTERVAL_HOURS`
- [ ] Provision Nextcloud quota per user (currently unlimited)
- [ ] Delete NC user when AssoCORE user is deleted (`DELETE /user/me` / `DELETE /user/{id}`)

### General

- [ ] Separate app database from the Nextcloud database (currently both share the same MariaDB instance and credentials)
- [ ] Request logging middleware
- [ ] Integration tests for the auth flow: register → login → protected route → 401 on bad token

---

## Frontend

### Auth (F1)

- [ ] `/login` page — username + password form calling `POST /user/login` (note: no `/api` prefix)
- [ ] JWT storage strategy (decide: `httpOnly` cookie vs `localStorage`) — note the API now returns an access **and** a refresh token
- [ ] `lib/api.ts` — fetch wrapper that injects `Authorization: Bearer <token>` and transparently calls `POST /user/refresh` on a 401, since access tokens now expire after 15 min
- [ ] Global auth state (Zustand or React context) seeded from `GET /user/me`
- [ ] Route guard — redirect unauthenticated users to `/login`
- [ ] `/register` page

### User Account

- [ ] `/account` page — view and edit profile, change password
- [ ] Notification bell in the nav with unread count badge

### Dashboard

- [ ] Main layout: sidebar nav, top bar, content area
- [ ] Dashboard home wired to `GET /user/me`

### Event pages (F3)

- [ ] Calendar view component
- [ ] Event creation form (admin only)
- [ ] Event detail page with registration button

---

## Infrastructure

- [ ] Set a strong `SECRET_KEY` via an environment secret in prod (not committed to `.env`)
- [ ] Separate MariaDB database for the app (distinct from Nextcloud's)
- [x] `GET /health` for the k8s liveness/readiness probes (static by design — a DB check there would restart healthy pods during a DB blip)
- [x] `.env.example` with placeholder values for new contributors
- [ ] Deeper healthcheck (e.g. `/ready`) that verifies DB and redis connectivity
- [ ] Watchtower exclusion rules so dev images are not auto-updated
