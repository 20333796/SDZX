# Repository Guidelines

## Project Structure & Module Organization

`apps/web` is the Vue 3, Vite, TypeScript, Router, and Pinia client. Keep route entry points in `src/pages/`, reusable domain work in `src/features/`, fallback data in `src/config/`, and shared API shapes in `src/types.ts`.

`apps/api` is the FastAPI service. Routers belong in `app/routers/`, persistence models in `app/models.py`, request and response contracts in `app/schemas.py`, and domain logic in `app/services/` or `app/modules/`. Alembic revisions live in `apps/api/alembic/versions/`; append revisions instead of changing an applied migration.

`apps/worker` runs independent document parsing. `infra/compose` provides the local deployable stack, while `infra/helm` defines production workloads. `docs/` holds ADRs, runbooks, delivery tracking, and third-party notices. Keep the legacy `prototype/` intact unless a task explicitly targets it.

## Build, Test, and Development Commands

Run from the indicated directory:

- `cd apps/web; npm run dev` starts the Vite client with an API proxy.
- `cd apps/web; npm run build` type-checks and produces the production bundle.
- `cd apps/api; python -m alembic upgrade head` applies database migrations.
- `cd apps/api; python -m pytest -q` runs API and domain tests.
- `docker compose -f infra/compose/docker-compose.yml up --build` starts web, API, PostgreSQL/pgvector, Redis, and MinIO.

GitLab validates the same build and test commands, audits dependencies, emits an API SBOM, and packages immutable images when a container registry is configured.

Use Python 3.12 and install API dependencies with `pip install -r requirements-dev.txt`. Copy `.env.example` to `.env`; never commit real passwords, OIDC values, or storage credentials.

## Coding Style & Naming Conventions

Use two-space indentation for Vue, CSS, JSON, and YAML; use four spaces for Python. Use kebab-case CSS classes, camelCase TypeScript values, PascalCase Vue components and Python models, and snake_case Python modules and API JSON fields. Preserve UTF-8, `lang="zh-CN"`, and Simplified Chinese UI copy. Make small, reviewable edits; do not use broad scripted replacements on Chinese files.

## Testing Guidelines

Add focused tests for API contracts, migrations, state transitions, and interpretation rules. Name Python tests `test_<behavior>`. Before visual changes are complete, check desktop and narrow layouts, anonymous chat modes, resource filtering, new-tab links, and browser-console errors. Document validation in the pull request.

## Commit & Pull Request Guidelines

Use concise scoped imperative commits, for example `api: add knowledge document state transition`. PRs should state the behavior change, affected paths, migration or configuration needs, validation commands, linked issue, and screenshots for UI changes. Do not describe roadmap placeholders as implemented algorithms.
