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
- [ ] Enforce RBAC: `Admin` role required for destructive routes (`DELETE /user/{id}`, future admin-only endpoints) — `Role` model exists but is never checked
- [ ] `GET /user/` should be admin-only, or return a reduced payload for non-admins
- [ ] Rate limiting on `POST /user/login` to prevent brute-force
- [ ] Change `SECRET_KEY` placeholder in `.env` before any deployment
- [ ] Refresh tokens (access tokens are 24 h with no revocation mechanism)

### Events (F3)

- [ ] Wire `back/app/routes/events.py` to the DB — models and schemas defined, all handlers return stubs
- [ ] `POST /event/{id}/register` and `DELETE /event/{id}/register` for member self-registration
- [ ] `POST /event/{id}/checkin` for attendance tracking (F4)

### Cloud / Apps (F2)

- [ ] Wire `back/app/routes/apps.py` to `nc-py-api` — provision a Nextcloud user on `POST /user/` so each member has their own storage
- [ ] Scope file access per authenticated user
- [ ] File upload endpoint

### General

- [ ] Separate app database from the Nextcloud database (currently both share the same MariaDB instance and credentials)
- [ ] Request logging middleware
- [ ] Integration tests for the auth flow: register → login → protected route → 401 on bad token

---

## Frontend

### Auth (F1)

- [ ] `/login` page — username + password form calling `POST /api/user/login`
- [ ] JWT storage strategy (decide: `httpOnly` cookie vs `localStorage`)
- [ ] `lib/api.ts` — fetch wrapper that injects `Authorization: Bearer <token>` on every request
- [ ] Global auth state (Zustand or React context) seeded from `GET /user/me`
- [ ] Route guard — redirect unauthenticated users to `/login`
- [ ] `/register` page

### User Account

- [ ] `/account` page — view and edit profile, change password
- [ ] Notification bell in the nav with unread count badge

### Dashboard

- [ ] Main layout: sidebar nav, top bar, content area
- [ ] Dashboard home wired to `GET /user/me`

### Events (F3)

- [ ] Calendar view component
- [ ] Event creation form (admin only)
- [ ] Event detail page with registration button

---

## Infrastructure

- [ ] Set a strong `SECRET_KEY` via an environment secret in prod (not committed to `.env`)
- [ ] Separate MariaDB database for the app (distinct from Nextcloud's)
- [ ] Healthcheck endpoint that verifies DB connectivity (current `GET /` is static)
- [ ] `.env.example` with placeholder values for new contributors
- [ ] Watchtower exclusion rules so dev images are not auto-updated
