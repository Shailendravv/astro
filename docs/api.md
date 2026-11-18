# API Contract — Jyotish Research Platform

> Status: DRAFT v0.3 (2026-11-17, post-review corrections: model placeholders, provenance fields, Chara Dasha gate, explicit Jaimini profile). Implementation: FastAPI in `apps/api/`. FastAPI's generated OpenAPI (`/api/openapi.json`) becomes the authoritative contract once code exists. Keep this document in sync with it.
> Related: [data-model.md](data-model.md), [architecture.md](architecture.md), [security.md](security.md).

## 1. General

- **Base URL:** `http://127.0.0.1:8000/api/v1` (localhost only in release 1).
- **Format:** JSON (UTF-8). Field names use `snake_case`. Enum values are lowercase strings.
- **Times:** ISO 8601. UTC values end with `Z`. Local birth date and time are sent as separate fields and never converted on the client.
- **Angles:** decimal degrees (`float`). A formatted `dms` string (e.g. `"23°14'05\""`) is included alongside for display.
- **IDs:** UUIDs for charts, readings, and runs. Stable text IDs for rules (`PAR-YOG-0012`), cases (`GC-KP-0003`), sources, and citations.
- **Language:** `Accept-Language: en | hi` controls error messages and display labels. Reading language is an explicit request field.
- **Pagination:** `?limit=` (default 50, max 200) and `?cursor=`. Responses include `next_cursor`.
- **Idempotency:** `POST /charts` is idempotent on `(birth_record_id, profile_id)` plus the current engine/ephemeris version, and returns the existing chart if there is one.
- **Versioning:** a breaking change gets a new prefix (`/api/v2`). Additive fields are allowed within v1.

## 2. Authentication

Release 1 (D-001): **no user authentication**. The API binds to `127.0.0.1` only, CORS allows only the local web origin (`http://127.0.0.1:3000`), and the database port is not published. See [security.md](security.md) §3.

Future multi-user: OIDC bearer tokens (`Authorization: Bearer …`) with roles `owner`, `reviewer`, `viewer`. Endpoints below list their intended role so that auth can be added later without redesign.

## 3. Errors

All errors use RFC 9457 `application/problem+json`:

```json
{
  "type": "https://jyotish.local/errors/nonexistent-local-time",
  "title": "Local time does not exist",
  "status": 422,
  "code": "NONEXISTENT_LOCAL_TIME",
  "detail": "02:30 on 1945-10-15 did not occur in Asia/Kolkata due to a clock change.",
  "params": {"options": ["shift_forward", "manual_offset"]},
  "trace_id": "01JD…"
}
```

| HTTP | `code` | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Schema/field validation failed (`errors[]` lists fields) |
| 404 | `NOT_FOUND` | Unknown ID |
| 409 | `CONFLICT` | Editing frozen dataset / immutable record; duplicate source checksum |
| 422 | `AMBIGUOUS_LOCAL_TIME` | Local time occurs twice; client must choose `earlier`/`later` |
| 422 | `NONEXISTENT_LOCAL_TIME` | Local time in DST gap |
| 422 | `OUT_OF_EPHEMERIS_RANGE` | Date outside 1800-01-01..2399-12-31 |
| 422 | `UNSUPPORTED_CALENDAR` | Date before 1582-10-15 |
| 422 | `HOUSE_SYSTEM_UNDEFINED` | e.g. Placidus at extreme latitude |
| 422 | `MODEL_NOT_VERIFIED` | Model ID not confirmed against the provider's official catalogue (decisions.md model register) |
| 422 | `PROFILE_REQUIRED` | A required profile was not chosen explicitly (e.g. Jaimini 7k/8k, which has no default, by owner decision on Q-006) |
| 409 | `METHOD_NOT_AVAILABLE` | Calculation method exists in the design but its research gate is not passed (e.g. `CHARA_KNRAO_*`, D-008) |
| 424 | `PROVIDER_ERROR` | LLM provider failed (`params.provider`, `params.retryable`) |
| 429 | `PROVIDER_RATE_LIMITED` | Provider rate limit |
| 500 | `INTERNAL_ERROR` | Unexpected; has `trace_id` |

## 4. Endpoints

### 4.1 System

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/health` | any | Liveness + DB + ephemeris files present |
| GET | `/version` | any | engine, ephemeris, tzdata, git commit, dataset versions |

### 4.2 Places

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/places?q=ujjain&limit=10` | owner | Offline GeoNames search → `[{geonames_id, name, admin1, country, lat, lon, tz_name, population}]` |

### 4.3 Birth records

| Method | Path | Purpose |
|---|---|---|
| POST | `/birth-records` | Create (original input stored unchanged) |
| GET | `/birth-records` | List |
| GET | `/birth-records/{id}` | Get, incl. normalized inputs |
| DELETE | `/birth-records/{id}` | Delete record and all derived charts/readings (US-1002) |

`POST /birth-records`
```json
{
  "label": "Test A",
  "birth_date_local": "1984-03-21",
  "birth_time_local": "05:42:00",
  "time_uncertainty_min": 5,
  "time_source": "certificate",
  "place_name": "Ujjain, Madhya Pradesh, IN",
  "geonames_id": 1253237,
  "latitude": 23.1793,
  "longitude": 75.7849,
  "tz_name": "Asia/Kolkata",
  "manual_utc_offset_min": null,
  "manual_dst": null,
  "override_reason": null,
  "ambiguity_choice": null
}
```
`201` → birth record + `normalized`:
```json
{
  "id": "0193…",
  "normalized": {
    "utc_datetime": "1984-03-21T00:12:00Z",
    "julian_day_ut": 2445780.508333,
    "utc_offset_min": 330, "dst_applied": false,
    "tz_resolution": "iana", "tzdata_version": "2026b",
    "warnings": []
  }
}
```

### 4.4 Calculation profiles

| Method | Path | Purpose |
|---|---|---|
| GET | `/profiles?tradition=kp` | List (key, version, status, settings, profile_hash) |
| GET | `/profiles/{key}/{version}` | Get one |
| POST | `/profiles` | Create new version (clone + edit); never mutates existing |

### 4.5 Charts

| Method | Path | Purpose |
|---|---|---|
| POST | `/charts` | `{birth_record_id, profile_key, profile_version?}` → chart (idempotent). `profile_key` is always required; for Jaimini it must be `jaimini-lahiri-7k` or `jaimini-lahiri-8k`, chosen explicitly (no default, owner decision on Q-006) |
| GET | `/charts/{id}` | Chart with positions, cusps, warnings, provenance |
| GET | `/charts/{id}/sensitivity?window_min=10` | Facts that change within ±window (US-106) |

Chart response (abridged; values are illustrative only, not reference data):
```json
{
  "id": "0193…",
  "tradition": "kp",
  "provenance": {
    "profile": {"key": "kp-krishnamurti", "version": 1, "hash": "9f2…"},
    "ayanamsha": {"name": "krishnamurti", "value_deg": 23.5712},
    "engine_version": "0.3.0", "ephemeris": "pyswisseph 2.10.3.2",
    "tzdata_version": "2026b", "git_commit": "a1b2c3d"
  },
  "positions": [
    {"body": "moon", "tropical_lon": 147.21, "sidereal_lon": 123.64, "dms": "3°38'24\" Leo",
     "sign": "leo", "nakshatra": "magha", "pada": 2, "speed": 13.1, "retrograde": false}
  ],
  "cusps": [{"house": 1, "sidereal_lon": 331.02}],
  "warnings": [{"code": "NEAR_SUB_BOUNDARY", "subject": "cusp.10",
                "distance_arcsec": 41.0, "time_to_cross_min": 2.7}]
}
```

### 4.6 Tradition outputs

All return a `FactSet` (`facts[]` with `fact_id`, `value`, `rule_ids`, `status_of_rules`) plus a view-friendly structure.

| Method | Path | Purpose |
|---|---|---|
| GET | `/charts/{id}/parashari/basics` | Lordships, dignities, graha drishti |
| GET | `/charts/{id}/parashari/yogas?include_near_miss=false` | Yogas with conditions/exceptions |
| GET | `/charts/{id}/parashari/shadbala` | All components |
| GET | `/charts/{id}/parashari/vargas/{varga}` | Release 1 accepts only `D1`, `D2`, `D3`, `D7`, `D9`, `D10`, `D12`, `D30` (D-009); others → `400 VALIDATION_ERROR` |
| GET | `/charts/{id}/parashari/dashas/vimshottari?levels=3&from=&to=` | Periods |
| GET | `/charts/{id}/kp/lords` | Star/sub/sub-sub lords for planets and cusps |
| GET | `/charts/{id}/kp/significators` | Four-level significators with derivation |
| POST | `/kp/ruling-planets` | `{datetime_utc?, latitude, longitude, profile_key}` (defaults to now) |
| GET | `/charts/{id}/jaimini/karakas` | Chara Karakas + tie flags |
| GET | `/charts/{id}/jaimini/rashi-drishti` | Sign aspects |
| GET | `/charts/{id}/jaimini/argala` | Argala/Virodhargala per house |
| GET | `/charts/{id}/jaimini/dashas/{method}` | Jaimini dasha periods. **Release 1: no method is available yet.** `CHARA_KNRAO_*` returns `409 METHOD_NOT_AVAILABLE` (with `params.status: "under_research"`, `params.decision: "D-008"`) until both D-008 gates are passed |

Calling a tradition endpoint on a chart computed with another tradition's profile returns `409 CONFLICT`. This keeps traditions from being mixed silently.

### 4.7 Readings

| Method | Path | Purpose |
|---|---|---|
| POST | `/readings` | Create reading (synchronous; SSE variant below) |
| POST | `/readings/stream` | Same, `text/event-stream`: `progress`, `claim`, `done`, `error` events |
| GET | `/readings/{id}` | Get with claims, validation result, provenance |
| GET | `/readings?chart_id=` | List |

`POST /readings`
```json
{
  "birth_record_id": "0193…",
  "mode": "comparative",
  "language": "hi",
  "question": "career prospects 2027-2029",
  "profiles": {"parashari": "parashari-lahiri", "kp": "kp-krishnamurti", "jaimini": "<jaimini-lahiri-7k | jaimini-lahiri-8k: chosen by the user>"}
}
```

`profiles.jaimini` is required whenever the mode uses Jaimini. There is no default (owner decision on Q-006); a missing value returns `422 PROFILE_REQUIRED`.
`201` →
```json
{
  "id": "0194…",
  "mode": "comparative",
  "language": "hi",
  "claims": [
    {"claim_id": "c1", "text": "…", "tradition": "kp", "basis": "source_rule",
     "fact_ids": ["kp.cusp.10.sub_lord"], "rule_ids": ["KP-SIG-0004"],
     "citation_ids": ["SRC-KP-READER4:ch3:p41"], "confidence": "medium", "agreement": "disagree"}
  ],
  "summary": {"agree": ["…"], "disagree": ["…"], "silent": ["…"]},
  "children": ["0194…par", "0194…kp", "0194…jai"],
  "validation": {"passed": true, "errors": [], "repair_attempted": false},
  "provenance": {
    "git_commit": "<commit>",
    "provider": "anthropic",
    "requested_model_id": "<RUNTIME_MODEL_ID from configuration>",
    "model_id": "<exact model ID returned by the provider>",
    "model_params": {"temperature": 0.2},
    "prompt_versions": [{"key": "reading.compare.hi", "version": 3, "content_hash": "<sha256>"}],
    "minimiser": {"version": "<version>", "config_hash": "<sha256>"},
    "retrieved_rule_ids": ["KP-SIG-0004"],
    "retrieved_citation_ids": ["SRC-KP-READER4:ch3:p41"],
    "charts": [{"chart_id": "0193…", "profile": {"key": "kp-krishnamurti", "version": 1, "hash": "<sha256>"},
                "engine_version": "<semver>", "ephemeris": "<lib version>", "tzdata_version": "<version>",
                "inherited": true}],
    "tokens_in": 9120, "tokens_out": 1430, "cost_estimate_usd": 0.0
  }
}
```

Values in `<…>` are placeholders, not real IDs. No model ID is shown here; the real one is configuration and is recorded in the decisions.md model register (D-012). The `charts[]` block is **inherited** from the immutable chart records (data-model §5.2); it is not copied into the reading row.

If validation still fails after one repair attempt, the response is `201` with `validation.passed=false`, and the UI shows the reading as **unvalidated**, with its errors.

### 4.8 Knowledge

| Method | Path | Purpose |
|---|---|---|
| GET | `/sources` | List catalogue |
| POST | `/sources` | Multipart upload + metadata → ingestion job |
| GET | `/sources/{source_id}` | Metadata + ingestion/review progress |
| GET | `/sources/{source_id}/pages/{page_index}` | Image URL + text + review status |
| PATCH | `/sources/{source_id}/pages/{page_index}` | Correct text / set review status |
| GET | `/search?q=&mode=keyword\|semantic\|hybrid&tradition=&lang=&review_status=` | Passage search |
| GET | `/passages/{citation_id}` | Passage |
| GET | `/rules?tradition=&topic=&status=` | List rules |
| GET | `/rules/{rule_id}` | Rule with citations, relations, reviews, implemented_in, tests |
| POST | `/rules/{rule_id}/reviews` | Add a `rule_review` (`actor`, `review_type`, `verdict`, `evidence`; data-model §4.4). Owner SOURCE_APPROVAL can move a rule to VERIFIED (source-approved, not expert-validated). Rule YAML updated via git workflow |
| GET | `/glossary?q=` | Terms (IAST, Devanagari, en/hi gloss) |
| GET | `/jobs/{id}` | Background job status (ingestion, OCR, embedding, evaluation) |

### 4.9 Evaluation

| Method | Path | Purpose |
|---|---|---|
| GET | `/datasets` | Versions + frozen state |
| POST | `/datasets/{version}/freeze` | Freeze (409 if already frozen) |
| GET | `/cases?collection=&status=&dataset_version=` | Cases |
| GET | `/cases/{case_id}` | Case |
| POST | `/evaluation/estimate` | Cost/time estimate for a planned run |
| POST | `/evaluation/runs` | Body below |
| GET | `/evaluation/runs/{run_id}` | Status, aggregate, and full provenance (all `evaluation_run` fields, data-model §6.3) |
| GET | `/evaluation/runs/{run_id}/cases?passed=false` | Per-case results incl. runtime and judge model IDs and judge configuration (data-model §6.4) |
| GET | `/evaluation/runs/{run_id}/diff?baseline=` | New failures / fixes / unchanged |
| GET | `/evaluation/runs/{run_id}/spot-checks` | Sampling record (method, seed, eligible count, sample size, selected case IDs) and owner verdicts |
| POST | `/evaluation/runs/{run_id}/spot-checks` | `{case_id, repeat_index, owner_verdict: agree\|disagree\|unsure, notes}` → appends `spot_check_review` (run unchanged) |
| POST | `/evaluation/runs/{run_id}/decision` | `{decision: approved\|rejected\|override_approved, reason}` → appends `run_decision` (run unchanged) |

`POST /evaluation/runs` body (values in `<…>` are placeholders):
```json
{
  "dataset_version": "1.0.0",
  "suites": ["reading-en", "reading-hi"],
  "repeats": 3,
  "baseline_run_id": null,
  "runtime": {"provider": "anthropic", "model_id": "<RUNTIME_MODEL_ID>", "params": {}, "prompt_set": "v1"},
  "judge": {"provider": "anthropic", "model_id": "<EVAL_JUDGE_MODEL_ID>", "params": {},
            "judge_prompt": "judge.reading@1", "rubrics": ["rubric.reading@1"]},
  "confirm_cost": true
}
```

- `runtime` is omitted for Track D-only runs. `judge` is omitted when no tier 2 judging is requested.
- Both model IDs must be verified (`422 MODEL_NOT_VERIFIED` otherwise).
- The server sets `self_judged` when runtime and judge are the same provider + model ID.
- LLM-backed runs need `confirm_cost: true`. Otherwise the API returns `400` with the estimate.

### 4.10 Settings

| Method | Path | Purpose |
|---|---|---|
| GET/PUT | `/settings` | UI language, chart style, default profiles for Parashari and KP (Jaimini has none, by owner decision on Q-006), active runtime and judge model configuration |
| POST | `/providers/{provider}/verify-model` | `{model_id}` → checks that the ID appears in the provider's model list. This only confirms the ID exists; the owner still records the official-catalogue check (date, source, exact ID) in the decisions.md model register before activation |

## 5. CLI equivalents

Everything in §4.8 and §4.9 is also available from a CLI (`python -m jyotish …`) for Claude Code workflows, e.g. `jyotish eval run --dataset 1.0.0 --suites astronomy,kp`, `jyotish rules validate`, `jyotish ingest <file>`.
