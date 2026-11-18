# Jyotish Research Platform

Research-grade Parashari + KP + Jaimini platform: deterministic calculation engines, a source-grounded knowledge library, an LLM interpretation layer, and a golden-dataset evaluation framework. Release 1 is single-user and local (Docker Compose), in English and Hindi.

**Status:** M1 (project foundation). No astrology calculation exists yet. Nothing here is a Jyotish result.

- Rules for working in this repo: [CLAUDE.md](CLAUDE.md)
- Documentation index: [docs/](docs/) (start with [docs/implementation-plan.md](docs/implementation-plan.md) and [docs/decisions.md](docs/decisions.md))
- Licences and copyright notes: [docs/licensing.md](docs/licensing.md)

## Run it locally

Needs Docker Desktop (running), PowerShell, and a copy of this folder.

```powershell
scripts\init-env.ps1                      # creates .env with a random database password (once)
docker compose -p jyotish-dev up --build -d
```

Then open <http://127.0.0.1:3000> (health page) or <http://127.0.0.1:8000/api/v1/health>.

Stop with `docker compose -p jyotish-dev down`. **Never add `-v`** to the `jyotish` (local-prod) project: it deletes the database. See [docs/deployment.md](docs/deployment.md).

## Develop

```powershell
uv sync                                   # Python 3.12 environment from uv.lock
uv run ruff check . ; uv run ruff format --check .
uv run mypy
uv run lint-imports                       # tradition-isolation contracts
uv run pytest
npm --prefix apps/web ci
npm --prefix apps/web run lint ; npm --prefix apps/web run typecheck ; npm --prefix apps/web test
```

## Layout

| Path | What |
|---|---|
| `engine/` | Pure calculation code (no I/O, no LLM). `parashari`, `kp`, `jaimini` never import each other |
| `ai/` | Provider adapter, prompts, interpretation (M6) |
| `knowledge/` | Source catalogue, rule records (YAML), glossary. Books and extracted text are **never** committed |
| `evaluation/` | Golden datasets, evaluators, rubrics, baselines, reports |
| `apps/api/` | FastAPI service (`jyotish_api`) |
| `apps/web/` | Next.js UI (English + Hindi) |
| `tests/` | Unit, integration, regression, Track D checks |
| `scripts/` | Setup and repository checks |
