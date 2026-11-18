# Deployment & Operations — Jyotish Research Platform

> Status: DRAFT v0.3 (2026-11-17, post-review corrections: model ID variables). Release 1 runs on the owner's Windows 11 machine with Docker Desktop (WSL2 backend) (D-001, D-014).
> Related: [security.md](security.md), [architecture.md](architecture.md).

## 1. Environments

| Env | Where | Purpose | Data |
|---|---|---|---|
| `dev` | Owner's machine; API/web run with hot reload (in Docker or natively) | Development with Claude Code | Synthetic + owner's test data |
| `test` | CI runner, ephemeral Postgres container | Automated tests | Synthetic fixtures only |
| `local-prod` | Owner's machine, `docker compose` with release images | Daily use | Owner's real data and library |

`dev` and `local-prod` use **separate** Compose project names, volumes, and DB names, so development never touches real data.

## 2. Runtime topology (`local-prod`)

```
docker compose -p jyotish
├── db    postgres:17 + pgvector   volume: jyotish_pgdata     ports: none published
├── api   apps/api image           127.0.0.1:8000 → 8000     mounts: library (read-only), ephemeris data
└── web   apps/web image           127.0.0.1:3000 → 3000
```

- **Library root** lives on the host, outside the repo (PROPOSED `D:\JyotishLibrary\`), and is mounted read-only into `api` (read-write only for the ingestion job).
- **Ephemeris files** (`.se1`) are baked into the `api` image at a pinned version.
- **GeoNames** data is loaded into `db` by a one-time setup script.
- **Windows note:** the project path contains a space (`D:\AI Projects\astro`). Quote paths in scripts. Keep `.gitattributes` with `* text=auto eol=lf` so shell scripts work inside containers.

## 3. CI/CD

Git hosting: PROPOSED private GitHub repository with GitHub Actions (D-024).

**On every push / PR**

1. Lint & format: `ruff check`, `ruff format --check`, ESLint, Prettier.
2. Types: `mypy` (strict for `engine/`), `tsc --noEmit`.
3. Architecture: `lint-imports` (tradition isolation contracts).
4. Knowledge validation: `jyotish rules validate`, `jyotish cases validate`, frozen-dataset hash check, prompt version-bump check, i18n key check.
5. Tests: pytest unit + property + integration (Postgres service container), deterministic golden suites, Vitest.
6. E2E: Playwright + axe against `docker compose` stack (PRs only).
7. Security: gitleaks, `pip-audit`, and `node scripts/check-npm-audit.mjs` (fails on any high/critical npm advisory except those listed in `apps/web/audit-exceptions.json`, each with a reason and a review-by date; an expired exception fails the build). Also `scripts/check_repo_files.py` (no books, env files or large binaries).
8. Build images (tagged with commit SHA).

**M1 state (2026-11-18):** the workflow is `.github/workflows/ci.yml`. Every step was run locally and passed, but the workflow has **not run on GitHub** because the private remote does not exist yet (D-024, T1.2). Base images and Actions are referenced by tag; pin them by digest/commit SHA once the repository exists (security.md §2). The Track D stage exists and runs only layout checks until M2.

**Never in CI:** LLM-backed evaluation suites (cost, secrets). They run manually from the owner's machine (`jyotish eval run …`) and their reports are committed under `evaluation/reports/`.

**Release (manual)**

1. Tag `vX.Y.Z` on `main` → CI builds images tagged `vX.Y.Z`.
2. On the owner's machine: `scripts/release.ps1 vX.Y.Z`. The script backs up, pulls or builds images, runs `alembic upgrade head`, restarts, and runs a health check.

## 4. Environment variables

| Variable | Service | Example / default | Notes |
|---|---|---|---|
| `APP_ENV` | api, web | `dev` \| `test` \| `local-prod` | |
| `DATABASE_URL` | api | `postgresql+psycopg://jyotish:…@db:5432/jyotish` | |
| `POSTGRES_PASSWORD` | db | random | secret |
| *(no `API_BIND`)* | compose | n/a | The host-side bind address is fixed to `127.0.0.1` in `docker-compose.yml` and cannot be set from `.env`, so it cannot be widened by mistake (R1). Inside the container uvicorn listens on `0.0.0.0` |
| `ALLOWED_ORIGINS` | api | `http://127.0.0.1:3000` | CORS |
| `ALLOWED_HOSTS` | api | `127.0.0.1,localhost` | Host-header check |
| `NEXT_PUBLIC_API_BASE` | web | `http://127.0.0.1:8000/api/v1` | |
| `LIBRARY_ROOT` | api | `/library` (host `D:\JyotishLibrary`) | |
| `EPHE_PATH` | api | `/app/ephe` | Swiss Ephemeris data |
| `TZDATA_VERSION_PIN` | api | `2026b` | recorded with charts |
| `EMBEDDING_MODEL` | api | (local model name) | D-017 |
| `GROQ_API_KEY` | api | — | secret. There is no Anthropic key: the product uses no Anthropic model (D-030) |
| `RUNTIME_PROVIDER` | api | `groq` | The only real provider (D-030). Empty = AI features disabled |
| `RUNTIME_MODEL_ID` | api | *(no example in the repo; the owner sets it in the local `.env`)* | The Groq model ID recorded in the decisions.md model register (D-012). Must appear in the register before use. Never hard-coded in code, prompts, tests, or docs |
| `EVAL_JUDGE_PROVIDER` | evaluation | *(empty until the security.md §4 gate is approved)* | judge provider, recorded separately from the runtime provider. Owner proposal (Q-018): `groq`, same as the runtime, so runs are self-judged |
| `EVAL_JUDGE_MODEL_ID` | evaluation | *(empty until the gate is approved)* | evaluation judge model; deliberate evaluation runs only (D-022); never hard-coded. Owner proposal (Q-018): the same model as `RUNTIME_MODEL_ID` |
| `API_PORT`, `WEB_PORT` | compose | `8000`, `3000` | Host ports, always bound to `127.0.0.1`. Use different values for the `dev` project so it can run beside `local-prod` |
| `GIT_COMMIT` | api | set at image build | Returned by `/version` (reproducibility) |
| `PROMPT_SET` | api | `v1` | active prompt set |
| `LOG_LEVEL` | api | `INFO` | |
| `BACKUP_DIR` | scripts | `D:\JyotishBackups` | |

`.env.example` in the repo lists all of these without values. An empty model ID is valid configuration: the app starts, and AI features stay disabled (`MODEL_NOT_VERIFIED`) until a verified ID is set. Nothing before M6 needs a model ID. `scripts/init-env.ps1` creates a local `.env` from `.env.example` with a random database password and leaves every model setting empty.

## 5. Monitoring

A local single-user app needs little monitoring, but the following must exist:

- `GET /api/v1/health` (DB, ephemeris files, library mount) and `GET /api/v1/version`.
- Docker healthchecks on all three services; `restart: unless-stopped`.
- Structured JSON logs (`docker compose logs api`), no personal data, rotated by Docker log options (`max-size: 10m`, `max-file: 5`).
- LLM usage log: per call provider, model, prompt version, tokens, cost estimate, latency. Settings page shows monthly totals.
- Evaluation reports in `evaluation/reports/` are the quality monitor.
- Optional: Windows Task Scheduler job that runs `scripts/healthcheck.ps1` daily and the backup job.

## 6. Backup & restore

- **What:** Postgres (`pg_dump -Fc`), library root, `.env` (store separately in a password manager), `evaluation/reports` (already in git).
- **When:** automatically before every migration/release; scheduled daily (PROPOSED) via Task Scheduler; on demand from Settings.
- **How:** `scripts/backup.ps1` → dump + library archive → encrypted with `BACKUP_PASSPHRASE` → `BACKUP_DIR`, keep last 14 daily + 6 monthly. Copy to an external drive or cloud storage of the owner's choice. Everything stays encrypted.
- **Restore:** `scripts/restore.ps1 <backup-file>` → stop api/web → restore DB → restore library → `alembic upgrade head` → health check.
- Restore is tested before release 1 (T9.3) and then quarterly.

## 7. Rollback

| What changed | Rollback |
|---|---|
| App release | `scripts/release.ps1 <previous-tag>`; if migration was not backward compatible, restore pre-release backup |
| DB migration | `alembic downgrade -1` (all migrations implement downgrade) or restore pre-migration dump |
| Runtime model | Set `RUNTIME_PROVIDER`/`RUNTIME_MODEL_ID`/`PROMPT_SET` back to the previous approved baseline (plan §12 step 9); restart `api`. The judge settings (`EVAL_JUDGE_*`) are separate and do not change |
| Prompt set | Switch `PROMPT_SET` to the previous version; prompts are versioned, never edited in place |
| Calculation profile | Profiles are versioned; reactivate the previous version; existing charts keep their original profile |
| Rules / golden cases | `git revert`; loaders rebuild DB index on startup |

## 8. Routine operations (owner runbook)

| Task | Command |
|---|---|
| Start | `docker compose -p jyotish up -d` |
| Stop | `docker compose -p jyotish down` (never add `-v`; that deletes data) |
| Logs | `docker compose -p jyotish logs -f api` |
| Back up now | `scripts\backup.ps1` |
| Ingest a book | Library → Upload (or `jyotish ingest <file>`) |
| Run deterministic evaluation | `jyotish eval run --dataset <ver> --suites astronomy,chart,parashari,kp,jaimini` |
| Run LLM evaluation (Track I, deliberate only) | `jyotish eval run --dataset <ver> --suites reading-en,reading-hi,comparison-en,comparison-hi,adversarial-en,adversarial-hi --confirm-cost` |
| Rotate an API key | Update `.env` → `docker compose -p jyotish up -d api` → revoke the old key with the provider |
| Update tzdata | Bump `tzdata` package + `TZDATA_VERSION_PIN` → rerun astronomy suite → release |

## 9. First-time Git remote setup (T1.2, D-024)

State on 2026-11-18: the local repository exists on branch `main`, but **no remote** exists and the GitHub CLI (`gh`) is **not logged in**, so nothing has been pushed and GitHub CI has not run. The repository **must be created private** (Swiss Ephemeris AGPL, personal-data and copyright rules; [licensing.md](licensing.md) §2).

**Option A: GitHub CLI** (run in PowerShell from `D:\AI Projects\astro`)

1. `gh auth login` → GitHub.com → HTTPS → "Login with a web browser". Finish the browser step yourself.
2. `gh repo create jyotish-platform --private --source . --remote origin` (the name is a suggestion; do not add `--push` yet).
3. Confirm it is private: `gh repo view --json visibility,url` must show `"visibility":"PRIVATE"`. If it does not, stop and run `gh repo edit --visibility private --accept-visibility-change-consequences`.
4. `git push -u origin main`
5. Watch CI: `gh run list --limit 3`, then `gh run watch`. Share the result so failures can be fixed.

**Option B: website**

1. On github.com choose New repository, name `jyotish-platform`, select **Private**, and add **no** README, `.gitignore` or licence.
2. `git remote add origin https://github.com/<your-username>/jyotish-platform.git`
3. Check the repository page shows the "Private" label, then `git push -u origin main`.

If GitHub rejects the push with "GH007" (private email address), either use your `…@users.noreply.github.com` address in `git config user.email` for this repository, or turn off "Block command line pushes that expose my email" in GitHub email settings. Never paste a token or password into the chat or into any file in the repository.
