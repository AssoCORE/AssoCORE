# CLAUDE.md

AssoCORE is a self-hosted platform for running an association: members, events, files, payments.
It processes members' personal data, so GDPR applies to every change (see the last section).

| Directory | What it is |
|-----------|------------|
| `back/` | FastAPI API: async SQLAlchemy on MariaDB, redis for auth state, Nextcloud for files |
| `front/` | Next.js 16 app and BFF: the browser talks only to it, never to the API |
| `mobile/` | Flutter app |
| `docs/` | Astro documentation site, home of the GDPR register |
| `bruno/` | Bruno collection that walks through the API with tests: the backend demo without a frontend |
| `docker/`, `docker-compose.yml`, `k8s/` | Images, the dev/prod stack, the production manifests |

`back/` and `front/` have their own `CLAUDE.md` with what their code doesn't say by itself.

## Running

- Run `docker compose` from the repo root. The one `.env` there (copied from `.env.example`) feeds both the
  compose substitutions and the containers.
- `.env` sets `COMPOSE_PROFILES=dev`, so `docker compose up --wait` runs the hot-reload app.
  `--profile prod` builds the production images; `--profile mobile` / `mobile-prod` builds the APK into `build/mobile/`.
- Compose stops and names any missing required variable (`${VAR:?}`). Fill it in `.env`.
- API on :8000 (Swagger at `/docs`), front on :3000, Nextcloud on :8081.

## Done means green

Before calling a change done, run the checks for what it touches and report the result. Name any check you
skipped and why.

| Touches | Check |
|---------|-------|
| `back/` | `cd back && uv run pytest` (offline: SQLite + fakeredis, no services needed) |
| any JS/TS | `npx @biomejs/biome@2.3.15 ci .` (`check --write .` fixes most of it; the version matches `biome.json`'s `$schema`) |
| `front/` | `cd front && pnpm lint && pnpm exec tsc --noEmit` |
| compose, Dockerfiles, env | `docker compose up --wait` |

The first three are the CI jobs that branch protection requires (`.github/workflows/ci.yml`).

## Testing what needs a person

When checking something that needs someone clicking or typing (a form, navigation, an auth redirect, a Flutter
screen), give the user a short numbered list of steps to try and what each should show, then wait for their
feedback. Run everything that needs no input yourself first: tests, lint, build, `curl` against the API.

## How we work

How this team works with Claude. When the user states a new working habit, authorization or preference,
or a check proves worth adding to *Done means green*, update this file directly, remove what no longer
applies, and say so in your reply. Knowledge about the code goes to `back/CLAUDE.md` or `front/CLAUDE.md`
instead: one line with its reason, added after it caused a real surprise.

### Workflow

0. When the user is thinking through a new feature and no issue exists yet, suggest `/grilling` once.
   The decisions it settles go into the issue body.
1. Work starts from an issue. When there is none, create it with the `new-issue` skill.
2. Branch `<kind>/issue-<N>/<slug>` (e.g. `task/issue-336/rework-claude-md`) off an up-to-date `origin/dev`.
3. Commit at each green checkpoint.
4. When asked to push, also open the PR if the branch has none: base `dev`, body from
   `.github/PULL_REQUEST_TEMPLATE.md`, `Closes #<N>`.

Problems found along the way that are outside the task (tech debt, unrelated bugs) go in your reply with an
offer to file them; file them once the user agrees.

### Git

- Commit often: a commit saves progress. Each commit is green, so history stays bisectable.
- Fold a fix into the commit it fixes while that commit is unmerged: `--amend` for the last one,
  `git commit --fixup <sha>` then `git rebase --autosquash origin/dev` for an older one.
- Separate features get separate commits, and so does any change the user asks to keep apart.
- Messages are `type(scope): lowercase imperative`, e.g. `fix(front/auth): close an open redirect`.
- Push only when asked. Push rewritten history with `--force-with-lease`, after `git diff <old-tip> <new-tip>`
  confirms that a rewrite meant to change only history changed no content. Check `origin` before saying what
  was or wasn't pushed.
- PRs are rebase-merged into `dev`, so history stays linear. Bring a stale or stacked branch up to date by
  rebasing onto `origin/dev` (`git rebase --onto origin/dev <old-base>` drops commits that already landed
  under new SHAs).
- The `mirror` job reports a branch "was not mirrored" when the Epitech mirror's LFS budget is exhausted.
  That quota is shared with the whole school and not caused by the branch.

### Choosing a solution

- Prefer configuration over code: no new script or dependency when a setting or an existing tool does the job.
- Say so when there is a better idea than the one proposed, and give an opinion when asked for one.
- Ideas that come up during the work are usually good: suggest them, and keep `ROADMAP.md` and the docs site
  in step with what gets built.
- Once a plan is agreed, continue until it is done or blocked.

## GDPR

Personal data is anything about an identifiable person: names, usernames, emails, phone numbers, messages,
payments, IPs, free text that mentions someone. Two rules hold everywhere in the repo:

- Logs carry IDs, never personal data: write `user %d`, never a username, email, message body, search term or token.
- A change that adds or changes personal data (a table, column, file, log line, form field or call to an external
  service) follows `.claude/rules/gdpr.md` in full. Read it before starting such a change, wherever it is.
