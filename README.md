# Jyotish Research Platform

Research-grade Parashari + KP + Jaimini platform: deterministic calculation engines, a source-grounded knowledge library, an LLM interpretation layer, and a golden-dataset evaluation framework. Release 1 is single-user and local (Docker Compose), in English and Hindi.

**Status:** M2 in progress (rule knowledge base built; no book ingested; no rule written yet). No astrology calculation exists yet. Nothing here is a Jyotish result.

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

## Rule knowledge base commands

Rules are YAML files in `knowledge/rules/<namespace>/`. Schema, lifecycle and examples: [docs/rule-schema.md](docs/rule-schema.md). The rule set is empty until the first rule is drafted.

```powershell
uv run jyotish rules validate [--strict] [--format json] [--against <git-ref>]
uv run jyotish rules list
uv run jyotish rules seal <RULE_ID>      # writes missing content hashes, never overwrites
uv run jyotish rules hash <RULE_ID>
uv run jyotish rules approve <RULE_ID> --version N [--reject --reason "..."]   # owner only, in a real terminal
```

| Command | What it does |
|---|---|
| `validate` | Checks every rule and source record. `--strict` turns warnings into failures (CI uses it). `--against <git-ref>` also checks that recorded history was not edited or removed since that commit. Exit code 0 = OK, 1 = problems found, 2 = bad usage. |
| `list` | Shows each rule's status and whether runtime retrieval would serve it. |
| `hash` | Prints the content hash of a rule version. |
| `seal` | Writes a missing content hash. It never overwrites an existing one. |
| `approve` | Records the owner's source approval (VERIFIED) or rejection. It refuses to run without an interactive terminal and asks you to type the exact rule ID. Claude Code never runs this. |

Run these from the repo root. An approval means "source-approved", not "expert-validated".

## Layout

| Path | What |
|---|---|
| `engine/` | Pure calculation code (no I/O, no LLM). `parashari`, `kp`, `jaimini` never import each other |
| `ai/` | Provider adapter, prompts, interpretation (M6) |
| `knowledge/` | Source catalogue, rule records (YAML), glossary, and the rule validator/retrieval code (`knowledge/rulebase/`, see [docs/rule-schema.md](docs/rule-schema.md)). Books and extracted text are **never** committed |
| `jyotish_cli/` | The `jyotish` command: `uv run jyotish rules validate` etc. |
| `evaluation/` | Golden datasets, evaluators, rubrics, baselines, reports |
| `apps/api/` | FastAPI service (`jyotish_api`) |
| `apps/web/` | Next.js UI (English + Hindi) |
| `tests/` | Unit, integration, regression, Track D checks |
| `scripts/` | Setup and repository checks |
