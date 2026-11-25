# Backend

FastAPI with async SQLAlchemy (MariaDB in the stack, SQLite in tests), redis, and Nextcloud through `nc-py-api`.
`uv run dev` serves on :8000 outside Docker, given a reachable MariaDB.

## Routes

- Every module in `app/routes/` that exports `router: APIRouter` is mounted automatically, at the app root
  (`/user/...`, `/event/...`). There is no `/api` prefix.
- Put access gates on the router, `APIRouter(dependencies=[Depends(require_admin)])` or
  `require_roles("staff", "admin")`, so a route added later inherits them. `Depends(get_current_user)` handles
  token validation, revocation and the 401.
- List endpoints return `Page[T]` (`{items, total, limit, offset}`) through `paginate()` with
  `limit_param()` / `offset_param()`. Filter in SQL: filtering a page afterwards returns short pages and a
  `total` that disagrees with them.
- Pydantic schemas (`schemas/classes.py`) and ORM models (`db/models.py`) stay separate. Validation lives in
  the schemas, and `front/lib/auth/schemas.ts` mirrors the password, phone and email rules exactly: change both
  together, or users get 422s the form didn't warn about.
- `UserOut` deliberately carries no notifications or reminders: clients use their paginated routes.

## Database

- Async SQLAlchemy cannot lazy-load. Load the relationships a route reads with `selectinload` (`_user_q()` in
  `routes/user.py`; `_deletable_user_q()` for everything a cascading delete touches). A relationship read on
  every request declares `lazy="selectin"` on the model instead (`User.nc_account`).
- There are no migrations: `metadata.create_all` creates missing tables but never adds a column to an existing
  one, so a new field on a live model silently does nothing. Model new data as a new table (as
  `NextcloudAccount` is), or introduce Alembic.
- `DATABASE_URL`, when set, replaces the `MYSQL_*` variables entirely.

## Notifications

Only `core/notifications.py` writes the `notifications` table. Call `notify()` / `notify_many()` /
`notify_role()` after committing the work that triggered them. They commit or roll back on their own and
swallow every exception, so a failed notification costs only itself, provided the triggering work is already
committed. `POST /user/notification/` raises normally, since creating one is its whole purpose.

## Roles

Only `core/roles.py` `set_roles(session, user, names, changed_by)` changes a user's roles (the seeder aside).
It keeps `member` whatever it is given, refuses unknown names (`UnknownRoles` → 422) and demoting the last
admin (`LastAdmin` → 409), writes a `role_changes` audit row per grant or revoke, commits, then notifies the user
and runs every `on_roles_changed` hook. A feature reacting to role changes (chat channels, Nextcloud groups…)
registers a hook instead of being called from the route; hooks run after the commit, best-effort, failures
logged by ID. Changes apply on the next request: `get_current_user` reads roles from the database each time.

Schemas for a new domain go in their own module (`schemas/roles.py` is the first), not in `classes.py`.

## Background worker

`core/worker.py` runs one in-process loop, started in `lifespan`, on every backend replica. There is no broker:
redis isn't persistent in our deployments, so domain rows are the queue.
- Register work with `@poller("name", every=timedelta(days=1))` on `async def tick(session) -> int`, in a module
  the app imports at startup. Return how many rows were processed: the loop runs again at once while any
  poller finds work, and otherwise sleeps `WORKER_INTERVAL_SECONDS`. A poller with `every` waits its period only
  after a run that found nothing, so a batched purge drains its backlog.
- Rows claimed across replicas use `QueueRowMixin` + `claim()` / `complete()` / `fail()` (SKIP LOCKED with a
  lease, retries with exponential backoff). Delivery is at-least-once: a row in flight during a crash is
  claimed again, so its work must be safe to repeat.
- GDPR retention purges are pollers (`.claude/rules/gdpr.md`).
- `GET /health` reports the loop's last tick without failing on it: a growing `seconds_since_tick` means a
  stalled worker.

## Auth

- Access tokens last 15 min, refresh tokens 30 days. `POST /user/refresh` takes the refresh token in the body
  (no `Authorization` header: the access token is expected to be expired) and rotates it. The new token keeps
  its predecessor's expiry, so refreshing never extends a session.
- Replaying a used refresh token within `REFRESH_GRACE_SECONDS` (10 s) returns the same replacement pair, so
  concurrent tabs converge. Replaying it later counts as theft and revokes the whole token family.
- Revocation state lives in redis DB 1 (Nextcloud uses DB 0). With redis down, revocation checks are skipped
  (`AUTH_REDIS_STRICT=false`) but refresh and logout return 503.
- Rate limits key on the real client IP. The BFF sends it in `X-Client-IP`, proven by `BFF_SHARED_SECRET` in
  `X-BFF-Secret`. Without the right secret the header is ignored and the socket address is used, which is
  the Next.js server's and so one limit for everyone.

## Nextcloud

- Every user has a matching Nextcloud account. Its password derives from `SECRET_KEY` + username, unless the
  user linked their real account (`POST /nextcloud/link/init` → browser approval →
  `GET /nextcloud/link/poll/{handle}`), which stores an app password encrypted by `core/crypto.py` that
  `storage.py` prefers.
- Login re-checks the account at most every `NC_PROBE_INTERVAL_HOURS` and re-provisions it when missing,
  but never resets a linked account's password.

## Production secrets

- `SECRET_KEY`: a strong random value; the default is a placeholder.
- `BFF_SHARED_SECRET`: the same value on the backend and the frontend. In k8s it lives in its own `bff-secret`,
  read by both Deployments and generated by `k8s/01-secrets/create-app-secrets.sh`.
- `NC_APP_PASSWORD_KEY`: an independent Fernet key. It otherwise derives from `SECRET_KEY`, so one leak would
  decrypt every stored app password.
- `ADMIN_PASSWORD`: without it no admin account is seeded.
