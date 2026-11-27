# AssoCORE API: Bruno collection

A [Bruno](https://www.usebruno.com/) collection that walks through the backend API end to end. Each request has
tests, so a run is also a smoke test of a running stack. It shows every backend feature without the frontend.

## Setup (once)

1. Start the stack from the repo root: `docker compose up --wait`.
2. Copy `bruno/.env.example` to `bruno/.env`, then set `ADMIN_PASSWORD` to the value in the repo-root `.env`.
   `bruno/.env` is gitignored.

## Run it

**In the Bruno app**: *Open Collection* → pick the `bruno/` folder → select the **local** environment (top right)
→ right-click the collection → *Run*. Or click through the requests one by one: each has a short **Docs** tab
saying what it shows.

**From the terminal**, in `bruno/`:

```bash
npx @usebruno/cli run --env local
```

Every request's tests are listed, followed by a pass/fail summary.

## What a run does

Folders run in order, and each uses what the previous ones created:

| Folder | Shows |
|---|---|
| 01 Health | Liveness and readiness (database, redis) |
| 02 Auth | Admin login; a demo member is registered and logs in; token refresh and rotation; bad credentials refused |
| 03 Users | Profile, rectification, admin search (paginated), a member refused the user list |
| 04 Notifications | Admin to member, read state, broadcast to a role, members can't send |
| 05 Reminders | A member's own reminders |
| 06 Events | Create, register, double registration refused, check-in, members can't create |
| 07 Storage | Folder, upload, list, download, delete in the member's Nextcloud space (needs Nextcloud) |
| 99 Cleanup | Logout revokes the token, then the demo member is deleted (GDPR erasure) |

The admin's token (`accessToken`) is the default auth for every request. Requests that need a member's point of
view override it with `memberToken`. Each run registers a new demo member (`demo_<timestamp>`) and deletes it at
the end, so runs leave nothing behind.

**Login is rate-limited** to 5 attempts per minute per client, and a run makes 3. Two full runs within the same
minute therefore end in `429`: wait a minute between them.

## Adding requests

A backend PR that adds or changes a route adds its request here, in the matching folder, with tests for the
success case and for the main refusal (403, 409, 422…). Copy an existing `.bru` file for the format. Keep `seq`
in order, and set `auth: inherit` (admin), `auth: none` (public) or a `memberToken` bearer.
