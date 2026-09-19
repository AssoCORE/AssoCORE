# AssoCORE Frontend

Next.js TypeScript application using shadcn/ui on Tailwind.

## Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI**: shadcn/ui (new-york style) over Radix primitives, Lucide icons
- **Forms**: react-hook-form + zod
- **Code quality**: Biome formats and lints (config at the repo root); ESLint adds
  the Next-specific `core-web-vitals` rules Biome has no equivalent for

## Getting Started

Normally you run the whole stack from the repository root, which serves the
frontend on :3000 with hot-reload:

```bash
docker compose up --wait
```

To run only the frontend against a backend you started separately:

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

`BACKEND_URL` is the base URL the Next.js **server** uses to reach FastAPI
server-to-server — the browser never calls the backend directly, which is what
sidesteps CORS. It has no `NEXT_PUBLIC_` prefix, so it is never exposed to the
browser. It defaults to `http://localhost:8000` (`lib/backend.ts`), and Compose
overrides it to the backend service name; set it in `front/.env.local` only if your
backend is somewhere else.

## Adding shadcn Components

```bash
pnpm dlx shadcn@latest add button
```

If this fails with `Command failed with exit code 1: pnpm add -- cn`, that is pnpm's
build-approval gate making the CLI's internal `pnpm add` exit non-zero even though
the install succeeded. Run `pnpm approve-builds` once and retry.

Components import the local `cn()` helper from `@/lib/utils`.

## Project Structure

```
front/
├── app/              # Next.js app router (routes + /api/auth handlers)
├── components/
│   ├── auth/        # AuthProvider, LogoutButton
│   └── ui/          # shadcn UI primitives
├── lib/
│   ├── auth/        # session, roles, cookies, jwt, schemas
│   └── backend.ts   # server-to-server fetch wrapper
├── proxy.ts          # runs before protected pages; refreshes expired tokens
└── public/           # Static assets
```
