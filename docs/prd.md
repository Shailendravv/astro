# Product Requirements — Jyotish Research Platform (Parashari + KP + Jaimini)

> Status: DRAFT v0.3 (2026-11-17, post-review corrections). Source plan: [../integrated_jyotish_project_plan.md](../integrated_jyotish_project_plan.md).
> Related: [user-stories.md](user-stories.md), [architecture.md](architecture.md), [decisions.md](decisions.md).

## 1. Problem

Jyotish software usually does one of two things. It hides calculation conventions (ayanamsha, node type, house system) behind defaults, or it blends Parashari, KP, and Jaimini rules into one reading with no indication of which tradition a statement comes from. AI chat tools make this worse: they invent rules and citations, improvise calculations, and present uncertain interpretations as settled.

The project owner wants a research-grade tool with these properties:

- Calculations are correct, reproducible, and use explicit conventions.
- Each tradition is applied on its own terms.
- Every classical claim traces to a specific source, edition, and verse/page.
- AI helps with research and interpretation without becoming the source of truth.
- Quality is measured against a frozen benchmark, so the AI model can be changed later without silent regressions.

The owner is **not** a Jyotish specialist or a programmer, so the system and its documentation must make correctness visible without requiring expert review of code.

## 2. Users

| User | Description | Release 1 |
|---|---|---|
| **Owner / researcher** | The only user. Enters birth data, reads charts, requests readings, manages the book library, approves sources and evidence for rules and golden cases, runs evaluations. Reads English and Hindi. Not expected to provide specialist Jyotish validation ([testing.md](testing.md) §7). | ✅ |
| Reviewer (expert astrologer) | Invited to review rules or golden cases | ❌ Future: needs multi-user (D-001) |
| Client / end user | Receives readings | ❌ Future |

The owner wears several hats in release 1: researcher, source approver, and evaluator. The UI keeps those activities separate. Owner approval confirms source and evidence; independent expert validation is recorded separately, and only when it actually exists.

## 3. Goals

1. **G1 – Trustworthy calculations.** Astronomical and chart calculations match independent references within defined tolerances, and every chart records its conventions.
2. **G2 – Three distinct engines.** Parashari, KP, and Jaimini are implemented as separate, tested systems that do not borrow each other's rules.
3. **G3 – Source-grounded knowledge.** A searchable library of texts, translations, and commentaries, plus rule records that each cite their source.
4. **G4 – Honest AI interpretation.** Readings attribute every point to a tradition, separate facts from rules from inference, cite sources, and say when evidence is missing or the traditions disagree.
5. **G5 – Measurable quality.** A versioned golden dataset and evaluation framework validate the system and gate every model or prompt change.
6. **G6 – Manageable for a non-specialist.** Clear docs, explicit decision records, and dashboards that show what passes and what fails.

## 4. Features (release 1)

### F1 Birth data & chart calculation

- Enter date, local time, place (offline place search), and birth-time uncertainty (± minutes) with its source (certificate, family recall, rectified).
- Automatic historical time-zone resolution with visible offset, DST, and manual override. Warnings for ambiguous or nonexistent local times and pre-1955 Indian local times.
- Store the original input separately from normalized input.
- Calculate with an explicit calculation profile per tradition (ayanamsha, node, houses, etc.). Parashari and KP each have one Release 1 profile. For Jaimini, the user must explicitly choose the seven-karaka or eight-karaka profile; nothing is preselected (D-007, Q-006).
- North-Indian and South-Indian chart display; tabular positions.
- Boundary warnings (sign, nakshatra, pada, KP sub, cusp) and a birth-time sensitivity report.

### F2 Parashari engine

- Graha drishti, sign/house lordship, dignity and condition.
- Yogas with conditions, exceptions, and cancellations, each linked to a rule ID.
- Shadbala with all components shown.
- Divisional charts, tranche 1: D1, D2, D3, D7, D9, D10, D12, D30 (D-009).
- Vimshottari Dasha to at least 3 levels (MD/AD/PD).

### F3 KP engine

- Star lord, sub lord, and sub-sub lord for planets and cusps.
- Placidus cusps and cuspal sub-lords.
- Significators (four-level scheme) for houses and planets.
- Ruling planets for a given moment and place.

### F4 Jaimini engine

- Chara Karakas under two separate profiles, 7-karaka and 8-karaka (D-007), with tie handling shown.
- Rashi Drishti, Argala and Virodhargala.
- Chara Dasha per K.N. Rao: **planned, under research, not available.** It is being specified step by step from the exact publication (D-008). It appears as a usable feature only after the D-008 implementation and availability gates are passed. Until then it is shown as "under research", and no substitute method is offered. Release 1 may ship without it.
- Karakamsha and the core sign- and karaka-based indications.

### F5 Readings

- Modes: Parashari only, KP only, Jaimini only, comparative (side by side), combined (synthesis with per-point attribution).
- English or Hindi output.
- Each claim shows tradition, basis (calculated fact / source rule / inference / uncertainty), and citations, and can be expanded to the underlying facts and passages.
- Agreement / disagreement / silence summary across traditions in comparative and combined modes.

### F6 Book library

- Import scans/PDFs (kept unchanged, outside git), with catalogue metadata and usage rights.
- Text extraction / OCR with page mapping and per-page review status.
- Search by keyword and meaning, filtered by tradition, source, and language. Side-by-side passage and page-image view.

### F7 Rule knowledge base

- Rule records with ID, tradition, terms, source and locator, original text and translation, conditions, exceptions, formal spec, alternatives, status, and history.
- Browse and filter rules; see which engine code and which tests reference each rule.

### F8 Golden dataset & evaluation

- Golden cases in the eight collections from plan §10.1, with statuses VERIFIED / PROVISIONAL / CONFLICTING_SOURCES / REJECTED.
- Dataset freezing and versioning.
- Evaluation runs by suite, model, and prompt version; per-category and per-case reports; diff against baseline.
- Model migration workflow (plan §12) with recorded approval.

### F9 Settings

- Calculation profiles (view, clone, edit as a new version).
- AI provider/model configuration, verified IDs only.
- UI language (en/hi), chart style, number/degree format.

### F10 Data management

- Export a chart or reading (JSON and PDF/print view).
- Delete a birth record and everything derived from it.
- Backup and restore of database and library (see [deployment.md](deployment.md)).

## 5. Scope

**In scope for release 1:** F1–F10 as above, single user, local Docker Compose, English + Hindi.

**Deferred to later releases:**

- Remaining Shodashavarga charts (D16, D20, D24, D27, D40, D45, D60).
- Additional Jaimini dashas (Narayana, Sthira, etc.).
- Transit (gochara) analysis and KP horary (Prashna) workflows beyond ruling planets.
- Ashtakavarga.
- Multi-user accounts, sharing, reviewer roles.

## 6. Non-goals

- **Not** a claim of scientific validity of astrological predictions (plan §16). Passing evaluation shows consistency with approved specifications, nothing more.
- **Not** a consumer horoscope app, daily predictions feed, or matchmaking service.
- **Not** automatic birth-time rectification.
- **Not** an LLM that calculates charts. LLMs never produce positions, lords, or dasha dates.
- **Not** a public or hosted service in release 1. No payments, no signups.
- **Not** silently blending traditions or choosing between conflicting sources.
- **Not** a redistribution channel for copyrighted books.

## 7. Success metrics

Thresholds are **PROPOSED** and get confirmed when the first golden dataset is frozen (see [testing.md](testing.md) §6).

| Metric | Target (release 1) |
|---|---|
| Planetary longitude vs independent reference (1800–2399) | ≤ 1 arcsecond max error on astronomy suite |
| Categorical chart outputs (sign, nakshatra, pada, lords, sub-lords, karakas) on VERIFIED cases | 100% |
| Dasha start dates vs reference cases | Exact to the day (given same year-length convention) |
| Invented citations in readings (citation IDs not in catalogue) | 0 in released runs (blocked by validator) |
| Tradition misattribution on `comparison-*` suites | 0 on VERIFIED cases |
| Interpretation rubric score (per tradition, per language) | ≥ agreed threshold, reported per category, never as one global score |
| Hindi readings | Same pass criteria as English on `reading-hi`, `comparison-hi`, `adversarial-hi` (D-029) |
| Rules implemented with source citation + tests | 100% of implemented rules |
| Owner can find, for any reading claim, its source passage | ≤ 2 clicks |
| Model migration | Approved only when all category thresholds pass; previous baseline retained |

## 8. Assumptions and open questions

- The owner supplies the book collection; editions and rights are recorded per source (plan §17 item 11; tracked as D-011 in [decisions.md](decisions.md)).
- The product uses no Anthropic model (D-030). The Groq model identifier was checked against Groq's official catalogue on 2026-11-18 and recorded in the decisions.md register (D-012); it is a Preview model, so availability is re-checked before each deliberate evaluation run (Q-019).
- All calculation conventions marked PROPOSED in [decisions.md](decisions.md) need owner confirmation before the relevant engine is treated as final.
