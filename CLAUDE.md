# CLAUDE.md — Jyotish Research Platform

Research-grade Parashari + KP + Jaimini platform. Deterministic calculation engines, a source-grounded knowledge library, an LLM interpretation layer, and a golden-dataset evaluation framework. Release 1 is single-user and local (Docker Compose), with English + Hindi.

The owner is not a programmer or Jyotish specialist. Explain tradeoffs plainly and record decisions instead of making them silently.

## Where docs live

| Need | Read |
|---|---|
| Original plan | `integrated_jyotish_project_plan.md` |
| What & why | `docs/prd.md`, `docs/user-stories.md` |
| How it's built | `docs/architecture.md` |
| Schema | `docs/data-model.md` |
| Endpoints | `docs/api.md` |
| Screens | `docs/ui-ux.md` |
| Task order / DoD | `docs/implementation-plan.md` |
| Tests & thresholds | `docs/testing.md` |
| Security/privacy | `docs/security.md` |
| Run/ops | `docs/deployment.md` |
| Decisions (D-NNN) | `docs/decisions.md` |

Read the relevant doc before changing an area. Update it in the same change.

## Non-negotiable rules

1. **No LLM calculations.** Positions, lords, sub-lords, karakas, yogas, dashas come only from `engine/` code.
2. **Traditions stay separate.** `engine/parashari`, `engine/kp`, `engine/jaimini` never import each other (import-linter enforces it). Do not fill a missing KP/Jaimini rule with Parashari logic, or the reverse.
3. **Source before rule.** Every implemented rule has a YAML record in `knowledge/rules/<tradition>/` with ID (`PAR-|KP-|JAI-XXX-NNNN`), citation, conditions, exceptions, status. Tests reference the rule ID.
4. **No silent conventions.** Ayanamsha, node (`MEAN`/`TRUE`), houses, karaka scheme, dasha method, `dasha_year_days`, and boundary rules come from a versioned calculation profile. Engines have no fallback defaults; a missing setting is an error. A new or changed convention gets a `docs/decisions.md` entry. Never pick one quietly.
   - Profiles are separate objects: `parashari-lahiri`, `kp-krishnamurti` (KP-specific ayanamsha, Placidus), `jaimini-lahiri-7k`, `jaimini-lahiri-8k`. Changing one never changes another.
   - `karaka_scheme` and the Jaimini dasha method are independent. K.N. Rao Chara Dasha does not imply the 8-karaka scheme.
   - All undecided conventions stay **PROPOSED** with alternatives and verification requirements (D-003–D-010, D-025).
   - `dasha_year_days` is a **Vimshottari-only** setting. It is never used for Jaimini Chara Dasha (whose year length is still a D-008 research item).
   - Release 1 vargas are only D1, D2, D3, D7, D9, D10, D12, D30 (D-009).
5. **Preserve conflicts.** Disagreeing sources become separate rule records linked as alternatives. Never merge them into one "best" rule.
6. **Never invent citations or answers.** If no source supports a claim, say so. Rule status stays PROVISIONAL until the owner approves its source and evidence (see *Verification roles* below). Unresolved questions go into `docs/decisions.md` → Open questions (Q-NNN), not into code as assumptions.
7. **Reproducibility.** Provenance is stored or inherited exactly as in `docs/data-model.md` §5.2 (readings) and §6.3 (evaluation runs):
   - Charts: engine, profile hash, ephemeris, tzdata.
   - Readings: app commit, runtime provider + exact returned model ID, params, prompt versions + hashes, minimiser version; they inherit chart provenance.
   - Evaluation runs: runtime and judge configuration **separately**, plus rubric versions, dataset version + hash, and the self-judged flag.
8. **Two evaluation tracks (D-022).** Track D (deterministic, code-only, CI) and Track I (interpretation: automatic checks → evaluation judge model in deliberate runs only → owner spot-checks) are kept and reported separately. **No model** (Claude Code, the Qwen runtime, or any judge) is ever the sole authority for accepting golden answers it drafted: those need owner approval plus independent evidence. The judge is the same Groq model as the runtime (owner proposal, Q-018), so every run is self-judged; tier 2 verdicts are never the sole basis for VERIFIED.
9. **Build evaluation with the feature (D-028).** Every new rule or calculation ships with its golden cases in the relevant suite. Reading work ships with en **and** hi cases (`reading-*`, `comparison-*`, `adversarial-*`, D-029).
10. **Provider payloads are personal data (D-027).** Exact positions can identify a birth moment. Send only what `PayloadMinimiser` produces: categorical facts, rounded degrees, windowed dasha dates, no identifiers.
11. **Model IDs are configuration (D-012, D-030).** The product uses **no Anthropic model** (owner decision, 2026-11-18): the only runtime provider is Groq. Never write a model ID into code, prompts, tests, or docs; the one exception is the decisions.md model register, where an ID appears only after it was checked against the provider's official catalogue (date and source recorded). The runtime ID is set through `RUNTIME_MODEL_ID` in the local `.env`. Never guess an ID. Keep three roles distinct: runtime model (Groq Qwen), evaluation judge model (same Groq model as the runtime by owner proposal, Q-018; always self-judged), and research/review model (Claude Code, recorded as `{actor: CLAUDE_CODE}`; not an app setting). When the runtime and judge models are the same, the run is self-judged. The runtime model is a Groq **Preview** model that may be retired (Q-019): store the exact returned ID everywhere.

## Verification roles (`docs/testing.md` §7)

- **Claude Code (you):**
  - Find and record source passages with exact edition, chapter, page, and `citation_id`.
  - Draft PROVISIONAL rule records, tests, and golden cases.
  - Report ambiguities and conflicting sources; never resolve them silently.
- **Automated tests:** show that the code reproduces documented examples. Never describe a passing test as proof that a Jyotish rule is correct.
- **Independent reviewer or calculation:** record one only if it actually exists (name, stated qualifications or implementation/version, evidence). Never invent or imply one. The default is `independent_validation: NONE`.
- **Owner:** approves decisions, source use, and evidence (SOURCE_APPROVAL), and reviews important or disputed cases.
  - Do **not** ask the owner to perform specialist Jyotish validation.
  - Do **not** describe owner approval as expert validation.
  - Do **not** present the owner as a Jyotish expert.

## Prohibited actions

- Hard-coding or guessing model IDs. Use config; a Groq ID (D-012) is used only after it is verified against the official catalogue and recorded in the register.
- Adding any Anthropic API integration, key, or model to the product (D-030).
- Making any real (non-fake) Groq call, or setting `RUNTIME_*` / `EVAL_JUDGE_*` values, before the owner approves the provider configuration and data-handling requirements (`docs/security.md` §4 gate). Groq Zero Data Retention is UNCONFIRMED: never assume it is enabled, and send no real person's data meanwhile.
- Editing a frozen dataset version, a stored baseline, a finished evaluation run, or an existing prompt/rubric version in place. Create a new version or an append-only record.
- Marking a rule or golden case VERIFIED. Only the owner's SOURCE_APPROVAL does that, never a model review alone. VERIFIED means "source-approved", not "expert-validated".
- Implementing any K.N. Rao Chara Dasha step before its rule record cites the exact edition and is VERIFIED, or exposing Chara Dasha as usable before the D-008 availability gate is passed (D-008 rev. 3). Do not fill gaps from other Chara Dasha variants or general knowledge.
- Preselecting or defaulting a Jaimini karaka profile (7k/8k) anywhere. The owner decided on 2026-11-18 (Q-006) that the user must always choose explicitly.
- Treating a PROPOSED convention (D-003–D-010, D-025) or the PROPOSED spot-check rule (Q-012) as accepted, or describing a result built on one as final. Label such results provisional.
- Describing any Hindi evaluation as "calibrated" before Q-013 calibration is complete. (Hindi development and `-HI` cases are not blocked.)
- Ingesting any named book before the owner supplies the inventory (Q-014). Do not assume the owner owns any recommended book.
- Answering an Open question (Q-NNN) by assumption, or changing an ACCEPTED decision without a superseding entry.
- Bypassing `PayloadMinimiser` or adding full-precision positions, cusps, ayanamsha values, or IDs to provider payloads.
- Running LLM-backed evaluation suites or any paid API call without the owner's explicit go-ahead.
- Committing secrets, `.env`, books/scans/extracted copyrighted text, or real people's birth data.
- Sending names, birthplaces, or raw birth date/time to LLM providers (`docs/security.md` §4).
- Exposing services beyond `127.0.0.1`, or publishing the DB port.
- `docker compose down -v` against the `jyotish` (local-prod) project.

## Coding conventions

- **Python 3.12**, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic. `ruff` (lint + format), `mypy` (strict in `engine/`).
- `engine/` is pure: no I/O, no DB, no network, no global state; typed immutable inputs/outputs.
- Boundary math (nakshatra, pada, KP sub) uses exact arithmetic (`Fraction` / integer milli-arcseconds), not float equality.
- Tests: pytest + Hypothesis; name rule tests `test_<RULE_ID>_<what>`; LLM calls in tests use the fake provider.
- **TypeScript strict**, Next.js App Router, `next-intl`. All UI strings in `apps/web/messages/{en,hi}.json`, nothing hard-coded. Tradition shown by text and colour together, never colour alone.
- Commits: small and focused; reference story/rule/decision IDs (e.g. `US-301`, `KP-SUB-0001`, `D-006`).
- Windows host, path contains a space: quote paths; LF line endings via `.gitattributes`.

## Workflows

- **Add a rule:** search library → draft YAML (PROVISIONAL) with citation_id + quote, noting any ambiguity or conflict → implement in the tradition engine → tests with rule ID → golden case(s) → ask the owner to review the cited passage and evidence (source approval, not specialist validation).
- **Add a golden case:** YAML in `evaluation/datasets/<collection>/`, status PROVISIONAL, with evidence, acceptable alternatives, `independent_validation: NONE` unless one is actually recorded, and `drafted_by` as structured entries (e.g. `{actor: CLAUDE_CODE}`, or `{actor: MODEL, provider: <provider>, model_id: <exact ID returned>}` when a runtime/judge model drafted it). Reading/comparison/adversarial cases get a Hindi twin (`-HI`). Never add it to a frozen version.
- **Change a prompt:** new version file + bump; run `reading-*`, `comparison-*`, `adversarial-*` (en + hi) only after owner approval of cost.
- **Change a convention:** decision entry (or History line if PROPOSED) → new profile version → tests for the new option → old charts untouched.
- **Hit an unknown:** add a Q-NNN row in `docs/decisions.md` → link it from the decision → continue with work that doesn't depend on it.

## Commands

Working as of M1 (run from the repo root, quote the path: it contains a space):

| Task | Command |
|---|---|
| Create local `.env` (once; random DB password, no model settings) | `powershell -File scripts\init-env.ps1` |
| Start dev stack (needs Docker Desktop running) | `docker compose -p jyotish-dev up --build -d` |
| Stop dev stack | `docker compose -p jyotish-dev down` (never `-v` on `-p jyotish`) |
| Python env | `uv sync` |
| Lint / format check | `uv run ruff check .` · `uv run ruff format --check .` |
| Types (strict in `engine/`) | `uv run mypy` |
| Architecture contracts | `uv run lint-imports` |
| Repo guard (books, env files, big binaries) | `uv run python scripts/check_repo_files.py` |
| Python tests, no DB needed | `uv run pytest -m "not track_d"` |
| Track D stage (layout checks until M2) | `uv run pytest -m track_d` |
| DB integration test | set `TEST_DATABASE_URL` to a throwaway Postgres, then `uv run pytest -m integration` |
| Python dependency audit | `uv run pip-audit --skip-editable` |
| Web checks | `npm --prefix apps/web run lint` · `run typecheck` · `run format:check` · `test` · `run build` |
| Web e2e + axe (stack must be up) | `npm --prefix apps/web run test:e2e` |
| npm audit gate | `node scripts/check-npm-audit.mjs` |

Not built yet (do not run or invent): `uv run jyotish rules validate` (M2, T2.6), `uv run jyotish eval run …` (M3).
