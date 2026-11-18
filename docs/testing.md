# Testing Plan — Jyotish Research Platform

> Status: DRAFT v0.3 (2026-11-17, post-review corrections). Covers ordinary software tests (§1–5), the golden-dataset evaluation framework (§6, details in plan §10), split into **Track D** (deterministic) and **Track I** (interpretation scoring) per D-022, and verification responsibilities (§7).
> Related: [architecture.md](architecture.md), [data-model.md](data-model.md) §6, [implementation-plan.md](implementation-plan.md).

## 1. Test layers

| Layer | Tooling | Location | Runs |
|---|---|---|---|
| Unit (Python) | pytest | `tests/unit/` | Every commit (CI) |
| Property-based | Hypothesis | `tests/unit/` (marked `@pytest.mark.property`) | Every commit |
| Contract / architecture | import-linter, schema validators | CI step | Every commit |
| Integration (API + DB) | pytest + httpx + Postgres container | `tests/integration/` | Every commit |
| Reference astronomy | pytest vs Skyfield/JPL | `tests/regression/astronomy/` | Every commit (sampled), nightly or manual (full sweep) |
| Track D: source-fidelity and citation checks | validators, no LLM | `knowledge/`, `evaluation/` | Every commit, from M2 (§6.5) |
| Track D: calculation-engine golden suites | evaluation runner, no LLM | `evaluation/` | Every commit, from M4 (D-028, §6.5) |
| Track I tier 1 automatic reading checks | fake provider, validators | `tests/`, `evaluation/` | Every commit, from M6 |
| Frontend unit | Vitest + Testing Library | `apps/web/**/*.test.tsx` | Every commit |
| E2E | Playwright (+ axe) | `apps/web/e2e/` | Every PR |
| Track I tiers 2–3 (judge model + owner spot-checks) | evaluation runner with runtime provider + judge | `evaluation/` | **Deliberate runs only**, with cost confirmation |

**Rule:** the default CI pipeline never calls a paid LLM API. LLM provider calls in unit/integration tests use a recorded fake adapter.

## 2. Unit test requirements

- Every rule implementation has tests named with its rule ID, e.g. `test_PAR_ASP_0003_saturn_10th_aspect`.
- Every calculation has at least: a typical case, both boundaries, and an invalid-input case.
- Every engine function is pure. Tests do no I/O except loading fixtures.
- Tradition isolation: a test asserts that each tradition's FactSet references only its own rule-ID prefix.

### Property-based invariants (examples)

- Sidereal longitude ∈ [0, 360), and `sidereal = (tropical − ayanamsha) mod 360`.
- Nakshatra index = ⌊lon / 13°20′⌋, and pada index = ⌊(lon mod 13°20′) / 3°20′⌋.
- KP: concatenated sub spans in each nakshatra sum exactly to 13°20′. The table has exactly 249 entries when split at sign boundaries.
- Vimshottari: sum of Mahadashas = 120 × `dasha_year_days` days for every supported value (365.25 initial, D-025). Antardashas within a Mahadasha sum to the Mahadasha length.
- Changing only `dasha_year_days` changes only dasha dates, never lords or order.
- Jaimini: Chara Karaka assignment is a permutation of the eligible planets: 7 bodies under `SEVEN`, 8 under `EIGHT_WITH_RAHU` (D-007).
- Rahu and Ketu are exactly 180° apart under **both** `MEAN` and `TRUE` node settings (D-004).
- No engine function runs without an explicit profile value for ayanamsha, node, house system, karaka scheme, dasha method, or year length. Missing values raise a validation error (architecture §4).
- Round trip: local → UTC → local returns the same local time for non-ambiguous inputs.

## 3. Integration and E2E

- API: create birth record → chart (each profile) → each tradition endpoint → reading (fake provider) → delete cascade.
- Error mapping: each `code` in [api.md](api.md) §3 has a test.
- Readings: the validator rejects unknown fact/rule/citation IDs and cross-tradition attributions (fake provider returns crafted bad outputs).
- Single-tradition mode: a test asserts that the prompt payload contains no other tradition's facts or rules.
- Data minimisation (D-027): payload snapshot tests assert that the provider payload contains no name, label, birthplace, coordinates, raw birth date/time, birth-date dasha balance, database/chart IDs, full-precision longitudes, cusp degrees, or ayanamsha values. Any degree is rounded to the configured precision, and dasha dates appear only within the question window at the configured precision ([security.md](security.md) §4).
- Profile separation: creating a new version of `parashari-lahiri` leaves `jaimini-lahiri-7k`/`-8k` unchanged, and the reverse (D-003).
- E2E flows: new chart (incl. ambiguous time dialog), switch language en ↔ hi, KP lords table, comparative reading drill-down to a passage, run a deterministic evaluation and view the report.
- Accessibility: axe has no serious/critical violations on every main screen, in both languages.
- i18n: CI fails on missing keys in `hi.json` or `en.json`.

## 4. Edge cases (must have explicit tests and golden cases)

**Time & place**

- Midnight births (00:00:00) and 23:59:59 (date rollover in UTC).
- DST gap (nonexistent) and overlap (ambiguous) local times, e.g. US/Europe transitions.
- India pre-1955 local time standards; 1942–1945 war time; LMT births (no zone).
- Southern hemisphere; longitudes near ±180°; equator; latitudes near ±66.5°.
- Placidus undefined/unstable at high latitudes → `HOUSE_SYSTEM_UNDEFINED`.
- Dates at ephemeris limits (1800-01-01, 2399-12-31) and just outside them.
- Dates before 1582-10-15 → `UNSUPPORTED_CALENDAR`.
- Leap day (29 Feb), leap-second-adjacent UTC times.

**Positions & boundaries**

- Planet/lagna at exactly 0°00′00″ and 29°59′59.9″ of a sign.
- Exactly on nakshatra / pada / KP sub boundaries (start-inclusive rule, D-006).
- Within 1″ of a boundary on either side.
- Stationary planets (speed ≈ 0; retrograde flag stability).
- Sandhi lagna (ascendant near sign boundary) → warning and sensitivity output.
- Ayanamsha switch changes the sign or nakshatra (same input, two profiles).
- Mean vs true node puts Rahu/Ketu in different nakshatra/pada/KP sub (both results asserted).

**Tradition specifics**

- Parashari: yoga cancellation conditions (e.g. neecha bhanga variants as separate rule records); Shadbala component edge cases (combust, war between planets).
- KP: cusp sub-lord flips within ±1 minute of birth time; significators when a planet occupies no star of house owners.
- Jaimini: Chara Karaka ties (equal degrees) under each scheme; same chart under 7k and 8k profiles (karaka order differs as expected); Rahu near 0° or 30° in sign under 8k; Argala fully obstructed vs partially.
- Jaimini Chara Dasha (`CHARA_KNRAO_*`): every worked example in the exact edition of K.N. Rao's book reproduced as a golden case citing page numbers. Signs with two lords (Scorpio, Aquarius) and every rule step listed in D-008 covered. No Chara Dasha golden case is VERIFIED before its step rules are VERIFIED. These cases are written only after the D-008 implementation gate is passed. Passing them shows the code matches the book's examples, not that the method has been independently validated (§7).
- Vimshottari: Moon at 0° of a nakshatra (full balance) and at the very end (≈ zero balance), under each supported `dasha_year_days`.

**Interpretation & adversarial**

- A question no rule covers → must say evidence is insufficient.
- Prompt-injection text inside an OCR passage ("ignore previous instructions…") → must be treated as data.
- User asks the combined reading to "just tell me the final answer" → attribution still required.
- Conflicting sources → both shown, no manufactured consensus.
- Hindi reading on the same case → same facts, citations, and attributions as English.
- Adversarial prompts in Hindi (e.g. a Hindi request to drop attribution or to "confirm" a fabricated rule) → same refusals as English.

## 5. Test data

- **Synthetic charts only** in the repo: generated birth inputs (no real private individuals). Labels like `TEST-A`.
- Reference data for astronomy: Skyfield + JPL DE440/441 ephemerides (independent of Swiss Ephemeris).
- Tradition reference cases: worked examples from source books (cited by `citation_id`), cross-checked with at least one independent implementation where available. Note which software was used and its settings in `evidence`.
- Public-figure charts may be used only with a documented data source and reliability rating. Store them as golden cases with source notes, never as owner data.
- Fixtures live in `tests/fixtures/` and `evaluation/datasets/`. Large reference tables are generated by scripts in `scripts/` and checked in with their generator version.

## 6. Golden dataset evaluation

**Update 2026-11-18 (D-030):** the product uses no Anthropic model. Wherever this section says "Opus" or "the configured Opus model", read **"the evaluation judge model"** (owner proposal, Q-018: the same Groq Qwen model as the runtime) or, for the runtime, **the Groq Qwen model** recorded in the [decisions.md](decisions.md) model register. The structure below is unchanged. **Because judge and runtime are the same model, every Track I run is self-judged** (flag set, 25% spot-check rate, D-022) and tier 2 verdicts are weaker evidence than an independent judge would give; they are never the sole basis for VERIFIED. No tier 2 run happens before the first-real-call gate in [security.md](security.md) §4 is approved.

### 6.1 Two tracks (D-022)

| | **Track D: deterministic** | **Track I: interpretation scoring** |
|---|---|---|
| What | Calculations, rule application, citation existence and source fidelity | Open-ended readings, comparisons, combined syntheses |
| Correct answer | Exists (with tolerances) | Rubric criteria, required points, prohibited claims |
| Scored by | Code only | Tier 1 automatic checks → Tier 2 evaluation judge model (same model as the runtime, Q-018) → Tier 3 owner spot-checks |
| LLM involved | Never | Runtime model generates; judge model scores (deliberate runs only) |
| Runs in CI | Source-fidelity and citation checks from **M2**; calculation-engine suites from **M4** (§6.5) | Never in CI. Deliberate runs only: initial testing (Stage A), model migrations, material prompt changes |
| Reported | Per suite, per tradition | Per suite, per tradition, **per language**, per tier |

The two tracks are reported separately and never combined into one score.

### 6.2 Suites

| Track | Suite | Plan §10.1 collection | Languages |
|---|---|---|---|
| D | `astronomy` | 1 Astronomical reference | n/a |
| D | `chart` | 2 Shared chart | n/a |
| D | `parashari` | 3 Parashari | n/a |
| D | `kp` | 4 KP | n/a |
| D | `jaimini` (both 7k and 8k profiles; `CHARA_KNRAO_*` only after the D-008 gates are passed) | 5 Jaimini | n/a |
| D | `source-fidelity` (citation exists, supports rule, passage reviewed) | all | n/a |
| D | `sanskrit` (glossary/transliteration consistency, deterministic checks) | all | sa |
| I | `reading-en`, **`reading-hi`**: individual Parashari, KP, Jaimini readings | 6 Interpretation | en, hi |
| I | `comparison-en`, **`comparison-hi`**: comparative and optional combined readings, attribution | 7 Integration | en, hi |
| I | `adversarial-en`, **`adversarial-hi`**: ambiguity, conflict, injection, missing evidence | 8 Adversarial | en, hi |
| D + I | `regression`: previously passing cases vs baseline | all | all |

**Hindi suites (D-029):** each Hindi case mirrors an English case (case ID suffix `-HI`). Both share the same language-neutral expectations (fact IDs, rule IDs, citations, attribution, prohibited claims). Hindi cases add checks for Devanagari output, glossary-consistent terminology, and correct Sanskrit terms.

### 6.3 Methods per output type (plan §10.6)

| Output | Track | Method |
|---|---|---|
| Numeric (longitudes, cusps, ayanamsha, Shadbala) | D | Absolute tolerance per field |
| Categorical (sign, nakshatra, lords, sub-lords, karakas, yogas present) | D | Exact match |
| Dates (Vimshottari periods) | D | Exact day, given the profile's `dasha_year_days` |
| Rule application | D | Rule-based assertions on conditions/exceptions |
| Citations | D | Exist in catalogue + SUPPORTS relation in rule record + passage review status |
| Reading structure, IDs, attribution, prohibited claims, language/script | I, tier 1 | Automatic checks (validator + assertions) |
| Rubric criteria not decidable automatically (coverage of required points, faithful use of rules, quality of uncertainty statements) | I, tier 2 | Evaluation judge model with a versioned rubric and judge prompt |
| Judge verdicts | I, tier 3 | Owner spot-checks (sampling rule in §6.4) |
| Variability | I | N repeats (default 3); report worst and median |

A Track D pass shows that the code matches the documented expectation. It does **not** show that the underlying Jyotish rule is correct (§7).

### 6.4 Judge governance and spot-check sampling (D-022)

- The judge model scores **only** in deliberate evaluation runs: initial testing (Stage A), future model migrations, and material prompt changes. It never runs on ordinary user requests.
- **Runtime model, judge model, and research/review model are recorded separately** (data-model §6.3, §6.4, §6.1). They are never treated as interchangeable, even when the same model ID fills two roles.
- **No model is the sole authority for accepting golden answers it generated or proposed** (D-022, D-030). Golden cases record `drafted_by` and `reviewed_by`. A case with a model (Claude Code, Qwen, or any judge) in `drafted_by` needs owner approval **and** independent evidence (reviewed source passage or independent calculation) to become VERIFIED.
- When the runtime model and the judge model are the same (owner's provisional configuration, Q-018), the run is labelled **SELF_JUDGED** in every report and record, and the higher spot-check rate applies. Self-judged results are **advisory** and cannot independently establish VERIFIED status. The labelling and sampling rules are implemented and tested in `evaluation/policy.py` (pure functions; no model is called).
- Judge provider, exact judge model ID, judge prompt version + hash, and rubric version + hash are recorded per run and per scored case.
- **Hindi calibration:** before judge verdicts on `*-hi` suites are trusted, compare them with owner ratings on a Hindi calibration set (PROPOSED: ≥ 90% agreement, Q-013). Until then, Hindi tier 2 verdicts are advisory and every report labels Hindi tier 2 results **"uncalibrated"**. No result may be described as a calibrated Hindi evaluation before calibration is complete (owner direction 2026-11-18). Calibration does **not** block building Hindi functionality or `*-hi` cases.

**Spot-check sampling rule (PROPOSED, Q-012; provisionally accepted by the owner 2026-11-18, final status not yet approved and stays PROPOSED).** Applied per suite and language:

1. Review **all** failed cases.
2. Eligible passing cases = passing cases in that suite and language.
3. Sample size = 10% of eligible passing cases (25% if self-judged), rounded up.
4. If at least 5 eligible passing cases exist, the sample is at least 5.
5. If fewer than 5 exist, review all of them.
6. Never select more cases than exist.
7. Selection method (PROPOSED: random with a recorded seed).
8. The report records: method, seed, eligible count, sample size, selected case IDs.

In formula form: `sample = min(eligible, max(ceil(rate × eligible), min(5, eligible)))`.

### 6.5 Progressive build-up (D-028)

The framework grows with the project instead of arriving as one late phase:

| Milestone | Evaluation increment | Track | In CI from this milestone |
|---|---|---|---|
| M2 Library & research | Source catalogue checks; citation existence; `source-fidelity` checks; passage review workflow; golden-case + rule schemas and validators; PROVISIONAL cases drafted alongside each rule | D | Yes: schema, citation, and source-fidelity checks |
| M3 Evaluation core | Rule-record and source-attribution checks expand as the knowledge base grows; runner, comparators, report generator, dataset versioning/freeze, run metadata | D (+ I scaffolding) | Yes: expanded rule/attribution checks |
| M4 Astronomy | `astronomy`, `chart` calculation suites | D | Yes: **first calculation-engine suites** |
| M5 Engines | `parashari`, `kp`, `jaimini` suites and golden cases, grown feature by feature | D | Yes |
| M6 Readings | Tier 1 automatic reading checks (CI with fake provider); `reading-*`, `comparison-*`, `adversarial-*` (en + hi) cases; judge harness for deliberate runs; Hindi calibration set | I | Tier 1 checks only; no paid model calls |
| M7 Initial evaluation | First deliberate full run with the Groq Qwen runtime (judge = same model, self-judged, Q-018); dataset freeze v1.0.0; baselines | D + I | Track D only |
| M8 Qwen | Same frozen dataset against Qwen; migration report | D + I | Track D only |

**M2 progress (2026-11-18):** the rule-record and source-catalogue checks are running as a Track D CI stage (`tests/track_d/test_rulebase.py`, `jyotish rules validate --strict`, and the append-only history check; see [rule-schema.md](rule-schema.md) §11 for every code). The real rule set and catalogue are empty until the owner supplies the book inventory (Q-014), so on the real repository they currently pass trivially; the synthetic-rulebase unit tests in `tests/unit/rulebase/` carry the real coverage (a negative test per validator code, mutation-checked).

"From M4" in D-028 refers to the calculation-engine suites, not to every deterministic check. Source-fidelity checks run earlier. A feature is not done until its golden cases exist in the relevant suite ([implementation-plan.md](implementation-plan.md) §1).

### 6.6 Proposed acceptance thresholds (PROPOSED, confirm at T7.3)

| Category | Track | Threshold on VERIFIED cases |
|---|---|---|
| Astronomy positions | D | max error ≤ 1″ vs reference; ayanamsha value ≤ 0.1″ vs Swiss Ephemeris spec |
| Chart construction (categorical) | D | 100% |
| Parashari / KP / Jaimini deterministic | D | 100% |
| Source fidelity (invented or non-supporting citations) | D + I | 0 failures |
| Tradition attribution (`comparison-*`) | I | 0 misattributions, per language |
| Prohibited claims | I | 0 occurrences across all repeats, per language |
| Reading rubric (`reading-*`) | I | ≥ 85% of required points per tradition **and per language**; no category < 75% |
| Uncertainty handling (`adversarial-*`) | I | ≥ 90% of cases handled correctly, per language |
| Regression | D + I | No previously passing VERIFIED case fails, unless documented and approved |

Results are always reported per category and language, never as a single score (plan §10.6). A Hindi failure blocks approval the same way an English failure does.

### 6.7 When to run what

| Trigger | Suites |
|---|---|
| Every commit | Unit, property, integration, all Track D checks and suites available at that milestone (§6.5), Track I tier 1 checks with the fake provider (from M6) |
| Nightly / manual | Full astronomy sweep |
| Material prompt change | Track I suites affected (en + hi) with the current runtime model; **deliberate run, cost confirmed** |
| Initial evaluation (M7) | All suites on frozen v1.0.0 |
| Model migration | All suites on the frozen dataset (plan §12) |
| Dataset freeze | All suites with the current production config to establish the baseline |
| Payload minimisation change (D-027) | Track I comparison of minimised vs previous payload (once per change) |

### 6.8 Evaluation run metadata (plan §12)

Every run stores the fields in [data-model.md](data-model.md) §6.3, including:

- runtime provider, exact runtime model ID, parameters, and prompt versions + hashes;
- judge provider, exact judge model ID, judge prompt version + hash, and rubric version + hash (when a judge is used);
- dataset version + content hash, suites, git commit, engine version, profile and minimiser config versions;
- start/end timestamps, repeat count, self-judged flag;
- aggregate and per-case results;
- the spot-check sample record (§6.4).

A completed run is immutable. Owner decisions and spot-check verdicts are added as separate append-only records ([data-model.md](data-model.md) §6.5).

## 7. Verification responsibilities

Four separate kinds of assurance. None substitutes for another, and the documents never present one as another.

| Who | Does | Does **not** |
|---|---|---|
| **Claude Code** | Finds and records source passages; records exact edition, chapter, page, and `citation_id`; drafts rule records (PROVISIONAL); writes tests and golden cases; reports ambiguities and conflicting sources | Resolve ambiguities or conflicts silently; set VERIFIED; claim a rule is correct |
| **Automated tests** | Check that code reproduces documented examples and expected calculations: deterministic outputs, boundaries, tolerances, rule application | Prove that the underlying Jyotish rule is correct |
| **Independent reviewer or independent calculation** | Where one actually exists: checks the rule interpretation or calculation against an independent source, a qualified reviewer, or an independent implementation. Reviewer identity, stated qualifications, and evidence are recorded | Get assumed or invented. If none exists, the record says `independent_validation: NONE` |
| **Owner** | Approves project decisions and use of source material; reviews cited passages, evidence, unresolved conflicts, and important cases; approves source transcriptions (source approval) | Get represented as a qualified Jyotish expert, or be expected to establish specialist correctness personally |

**What VERIFIED means:** a VERIFIED rule or golden case matches its cited evidence, and the owner has approved that source and evidence ([data-model.md](data-model.md) §4.4, §6.1). Whether an independent check exists is recorded separately in `independent_validation`. VERIFIED alone is not a claim of expert validation. K.N. Rao Chara Dasha has additional gates (D-008 rev. 3).
