# AssoCORE Frontend

Next.js TypeScript application with shadcn/ui and Material-UI.

## Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Libraries**:
  - shadcn/ui (Tailwind-based components)
  - Material-UI (MUI) v7
- **Code Quality**: Biome (formatting)

## Getting Started

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

## Adding shadcn Components

```bash
pnpm dlx shadcn@latest add button
```

## Project Structure

```
front/
├── app/              # Next.js app router
├── components/       # shadcn components
│   └── ui/          # shadcn UI primitives
├── lib/             # Utilities
└── public/          # Static assets
```
