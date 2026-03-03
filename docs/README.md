# Documentation

Documentation files are avaliable in `src/content/docs` subfolder.

However, we recommend using starlight to have a clearer, more organized view of documentation
Starlight looks for `.md` or `.mdx` files in the `src/content/docs/` directory. Each file is exposed as a route based on its file name.

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)


## Installation

Starlight uses pnpm to compile. As such, you will need npm to install pnpm

1. Install npm (Ubuntu)
```
apt install npm
```

2. Install pnpm

```
npm install -g pnpm@latest-10
```

## Compilation

Inside of the project repository, use the following command:

```
pnpm --prefix docs dev
```

The project documentation should appear on `http://localhost:4321`

## Starlight Additional Commands

Some of those commands may broke Starlight documentation.
All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `pnpm install`             | Installs dependencies                            |
| `pnpm dev`             | Starts local dev server at `localhost:4321`      |
| `pnpm build`           | Build your production site to `./dist/`          |
| `pnpm preview`         | Preview your build locally, before deploying     |
| `pnpm astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `pnpm astro -- --help` | Get help using the Astro CLI                     |
