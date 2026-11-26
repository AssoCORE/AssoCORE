# Frontend

Next.js 16 App Router, React 19, TypeScript, Tailwind v4, shadcn/ui. `@/` is the `front/` root.

## Auth: the browser never sees a JWT

- Only same-origin routes in `app/api/` talk to the backend, server-to-server through `lib/backend.ts`.
  `BACKEND_URL` is server-only (no `NEXT_PUBLIC_`) and defaults to `http://localhost:8000`.
- `app/api/auth/{login,refresh}` set httpOnly `access_token` / `refresh_token` cookies on `path: "/"`.
  A narrower path stops the browser sending `refresh_token` on page navigations, which breaks the refresh below.
- `proxy.ts` (Next.js 16's renamed middleware) runs before every protected page. When the access token has
  expired, it calls `POST /user/refresh` itself and rewrites the cookies on both the request and the response,
  because Server Components cannot set cookies. `/api/auth/refresh` is the fallback for a client fetch that
  401s later in the page's life.
- `proxy.ts` decodes the token without checking its signature; the backend validates it on every call.
- Every backend call forwards the browser's IP in `X-Client-IP`, with `BFF_SHARED_SECRET` in `X-BFF-Secret`.
  The IP is the **last** `X-Forwarded-For` entry (written by Traefik, or by Next.js in dev): earlier entries
  are client-controlled.
- The layout guards, `(protected)/layout.tsx` and `(protected)/(admin)/layout.tsx`, are UX only: the backend
  enforces access by itself.
- `lib/auth/schemas.ts` mirrors the backend's password, phone and email validation exactly, so zod errors match
  the server's 422s. `lib/auth/roles.ts` mirrors its role names.

## Tooling

- Biome (root `biome.json`) formats and lints. ESLint (`pnpm lint`) is there only for Next's `core-web-vitals`
  rules, which Biome lacks. Formatting stays Biome's alone, with no Prettier.
- `components/ui/` is shadcn output: neither linter checks it, Biome still formats it. Add components with
  `pnpm dlx shadcn@latest add <component>`. If that fails with `pnpm add -- cn` exiting 1, the install worked
  but pnpm's build-approval gate tripped: run `pnpm approve-builds` and retry.
- Components import the local `cn()` from `@/lib/utils`. Rewrite any import of the standalone `cn` package
  that the shadcn CLI emits to use it.
- `lucide-react` has no imports yet but is the `iconLibrary` in `components.json`, so `shadcn add` emits Lucide
  imports: keep it.
- The pnpm version lives only in `package.json`'s `packageManager`, which CI and the Dockerfile both read.
  A dev container keeps its old global pnpm until `docker compose up --build`.
