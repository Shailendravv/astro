# UI/UX Specification — Jyotish Research Platform

> Status: DRAFT v0.3 (2026-11-17, post-review corrections: Jaimini profile selection, R1 varga list, Chara Dasha availability, provenance). Web app: Next.js + TypeScript in `apps/web/`, served on `http://127.0.0.1:3000`. Languages: English and Hindi (D-002).
> Related: [user-stories.md](user-stories.md), [api.md](api.md).

## 1. Principles

1. **Traceability is visible.** Every calculated value and every reading claim can be expanded to show its provenance (profile, rule, source).
2. **Traditions stay separate.** Each tradition has its own tab, colour, and text label. They meet only in the Compare and Combined views, where attribution is always shown.
3. **Uncertainty is loud.** Boundary warnings, PROVISIONAL/CONFLICTING rules, unreviewed OCR, and unvalidated readings get badges. They are never hidden in tooltips only.
4. **Built for a non-specialist.** Use plain-language explanations beside technical terms, with glossary hover for Sanskrit.
5. **Calm, dense, research-tool feel.** Tables before decoration. No horoscope-app styling.

## 2. Information architecture

```
┌ Top bar: Logo · Charts · Library · Rules · Evaluation · Settings · [EN | हिं]
│
├ Charts
│   ├ Chart list
│   ├ New birth record
│   └ Chart workspace (per birth record)
│        ├ Overview
│        ├ Parashari  (Basics · Yogas · Shadbala · Vargas · Vimshottari)
│        ├ KP         (Lords · Cusps · Significators · Ruling planets)
│        ├ Jaimini    (Karakas · Rashi Drishti · Argala · Chara Dasha [under research, not available])
│        ├ Readings   (new reading · history)
│        └ Sensitivity
├ Library      (Sources · Search · Page reviewer)
├ Rules        (Browser · Review queue)
├ Evaluation   (Datasets · Cases · Runs · Compare runs · Migration)
└ Settings     (Language · Chart style · Profiles · AI providers · Backup)
```

## 3. Screens

### S1 Chart list

- Table: label, birth date/time (local), place, time source, uncertainty, last opened.
- Actions: New, Open, Export, Delete (confirmation dialog states what gets deleted).
- Empty state: "No charts yet" + New button + short explanation of what the platform does.

### S2 New birth record (US-101, US-102)

- Fields: label; date (calendar plus typed input, DD-MM-YYYY shown, ISO stored); time (HH:MM:SS, 24h); uncertainty ± minutes; time source.
- Place: type-ahead search (offline) with results showing name, region, country, coordinates. "Enter coordinates manually" link.
- **Resolution panel** (live, before saving): time zone, UTC offset, DST, resulting UTC time, tzdata version.
  - Ambiguous time → radio choice "earlier / later occurrence".
  - Nonexistent time → choice "shift forward / enter manual offset".
  - Pre-1955 India → amber notice + optional manual offset with required reason.
- Profiles: three selectors.
  - **Parashari:** shows `parashari-lahiri`, the only R1 profile, with a "PROPOSED convention" badge linking to D-003.
  - **KP:** shows `kp-krishnamurti` (KP-specific ayanamsha, Placidus), the only R1 profile, with a "PROPOSED convention" badge linking to D-003/D-005.
  - **Jaimini:** **nothing preselected.** The user must pick one of two separate calculation profiles:
    - "Seven karakas (`jaimini-lahiri-7k`)"
    - "Eight karakas incl. Rahu (`jaimini-lahiri-8k`)"
  - Helper text under the Jaimini selector: "These are two different calculation profiles. Choosing one does not choose a Chara Dasha method, and Chara Dasha does not require either one." Submit stays disabled until a Jaimini profile is chosen (owner decision on Q-006: no default).
- Submit → creates record + three charts → opens S3.

### S3 Chart workspace: Overview

- Header strip: label, local + UTC time, place, **profile chips** per tradition (click → shows full settings + decision IDs).
- Left: chart diagram, North / South Indian toggle.
- Right: positions table (body, sign, D°M'S", nakshatra, pada, ℞, speed).
- Warnings panel: boundary warnings with "minutes to cross" (US-105).

### S4 Parashari tabs

- **Basics:** lordship table; dignity table; aspect grid (planet × house) labelled "Graha drishti (Parashari)".
- **Yogas:** list of cards. Each card has name (Sanskrit + en/hi), status badge, conditions checklist (✓/✗), exceptions checked, rule ID, citation link. Toggle "show near-misses".
- **Shadbala:** component table + bar chart of total vs required minimum (with a text table alternative).
- **Vargas:** varga selector listing **only** the Release 1 charts: D1, D2, D3, D7, D9, D10, D12, D30 (D-009). No other vargas appear, not even disabled. Diagram + table, method name shown.
- **Vimshottari:** balance at birth; expandable tree MD → AD → PD with dates; timeline bar with the current period highlighted.

### S5 KP tabs

- **Lords:** table of planets and cusps with sign, star lord, sub lord, sub-sub lord. Boundary proximity column.
- **Cusps:** Placidus cusp table; error state for undefined latitude with explanation.
- **Significators:** house × level (1–4) matrix; click a cell to see its derivation path.
- **Ruling planets:** date/time/place picker (default now, home location); result table.

### S6 Jaimini tabs

- **Karakas:** header names the chart's profile ("Seven karakas" or "Eight karakas incl. Rahu"); ordered table (AK…DK), degree used, Rahu method note (8k only), tie flags. To see the other scheme, the user creates a second chart with the other profile.
- **Rashi Drishti:** sign-to-sign aspect grid labelled "Rashi drishti (Jaimini)". Visually distinct from the Parashari aspect grid.
- **Argala:** per-house table of argala sources, obstructions, net.
- **Chara Dasha: under research (not available).**
  - The tab shows a status panel instead of periods: "K.N. Rao Chara Dasha is being specified from the exact edition of the source book. It will become available only after all eight calculation steps are documented and verified (decision D-008)."
  - It links to D-008 and lists open items (Q-007, Q-008, Q-009, Q-017).
  - No periods, dates, or other Chara Dasha variants are calculated or shown.
  - This changes only when the D-008 availability gate is passed. The tab then shows method name, edition, and source; a period tree with dates; and the karaka scheme used, if any (Q-007).

### S7 Readings (US-501…507)

- **New reading form:** mode (Parashari · KP · Jaimini · Compare · Combined), language (EN/हिं), optional question, profile summary, estimated cost/model shown.
- **Single reading view:** claims list. Each claim shows:
  - Tradition badge (colour + text: "Parashari", "KP", "Jaimini").
  - Basis label: *Calculated fact* · *Source rule* · *Inference* · *Uncertain*.
  - Confidence.
  - Expand → facts (with values), rule cards, passages (with OCR status), links to source page.
- **Compare view:** three columns (one per tradition), aligned by topic. Bottom summary: Agree / Disagree / Silent lists.
- **Combined view:** synthesis claims, each with "from: c2 (KP), c7 (Parashari)" chips, plus a tab bar to open the underlying single readings.
- **Unvalidated reading:** red banner "This reading failed validation", with the list of errors and a regenerate action.
- **Provenance footer:** everything shown comes from stored reading fields or immutable records the reading references (data-model §5.2):
  - runtime provider and exact model ID returned by the provider;
  - parameters; prompt versions + content hashes; minimiser version;
  - app git commit; time; tokens; cost.
  - Expandable: per chart, profile key/version/hash, engine, ephemeris, and tzdata versions (marked "from chart").

### S8 Sensitivity (US-106)

- Window slider (± minutes, default = recorded uncertainty).
- Table: fact · value at −N · birth · +N · changed?
- Summary: "N of M tracked facts are stable within ±X min".

### S9 Library

- **Sources:** table with title, tradition, language, rights, pages, % reviewed. Upload dialog with metadata form.
- **Search:** query box, mode (keyword / meaning / hybrid), filters (tradition, source, language, review status). Results show snippet, source, locator, review badge.
- **Page reviewer:** split view, page image on the left, editable text on the right. Buttons: Mark reviewed · Save correction · Next unreviewed. Keyboard shortcuts.

### S10 Rules

- **Browser:** filters (tradition, topic, status). Rule detail shows statement, conditions, exceptions, formal spec, citations (with quotes), alternatives/conflicts, review history, implemented_in, tests.
- **Review queue:** PROVISIONAL rules. Actions:
  - **Approve source & evidence** (moves the rule to VERIFIED);
  - **Mark conflicting**;
  - **Reject** (note required).
  - Approval is disabled, with the reason shown, if the rule has no reviewed citation.
  - Helper text: "Approving confirms that the rule matches its cited source. It is not a specialist validation of the Jyotish rule."
  - Rule detail shows `independent_validation` as **None recorded** or **Recorded** (with reviewer/source). It is never implied.

### S11 Evaluation (US-801…805)

- **Datasets:** versions, frozen state, case counts by collection and status. Freeze action with confirmation.
- **Cases:** filterable table; case detail with expected outputs, evidence, alternatives, prohibited claims, history.
- **Runs:** list (date, dataset version, runtime model ID, judge model ID, prompt set, self-judged flag, status). "New run" form has separate **Runtime** and **Judge** sections. Each takes only verified model IDs (unverified ones are shown disabled with a link to the model register). The form shows a cost estimate and requires confirmation.
- **Run report:**
  - Per-suite, per-tradition, and per-language pass rates (table + small bar chart), Track D and Track I shown separately.
  - Failed cases list with expected vs actual diff; never a single global score.
  - Provenance panel with every `evaluation_run` field (data-model §6.3).
  - **Spot-check panel:** sampling method, seed, eligible count, sample size, selected case IDs, and owner verdicts.
- **Compare runs / Migration:** baseline vs candidate per category; threshold pass/fail per category; Approve / Reject / Override (reason required). Each action adds a decision record; the run itself never changes.

### S12 Settings

- Language, chart style, number format (D°M'S" vs decimal).
- Profiles: list, view, clone-and-edit (creates a new version). Default profile choices exist only for Parashari and KP; Jaimini has no default (owner decision on Q-006).
- AI providers: key status (set/not set, last 4 chars). Separate **runtime model** and **evaluation judge model** fields, each with a Verify button and the model register status (verified on / source). The active runtime model is shown. Empty model IDs are allowed; AI features then stay disabled.
- Backup: last backup time, "Back up now", restore instructions.

## 4. Shared components

| Component | Notes |
|---|---|
| `TraditionBadge` | Colour + text label + icon shape; never colour alone |
| `BasisLabel` | fact / rule / inference / uncertain |
| `StatusBadge` | VERIFIED (shown as "Source-approved"), PROVISIONAL, CONFLICTING_SOURCES, REJECTED, UNREVIEWED, UNVALIDATED, UNDER RESEARCH; plus "Independent check recorded" when `independent_validation = RECORDED` |
| `ChartDiagram` | North/South Indian; SVG; accessible table twin |
| `DegreeText` | Formats D°M'S" / decimal per setting; Devanagari or Latin numerals per locale setting |
| `TermWithGloss` | Sanskrit term with hover/focus card (IAST, Devanagari, en/hi gloss) |
| `ProvenancePopover` | Chart: profile key/version/hash, engine, ephemeris, tzdata, git commit. Reading: adds runtime provider + exact model ID, params, prompt versions + hashes, minimiser version. Shows only stored or inherited fields (data-model §5.2) and labels inherited ones |
| `CitationLink` | citation_id → passage drawer |
| `WarningList` | Boundary/time-zone/range warnings |
| `PeriodTree` | Dasha hierarchy with dates |
| `ConfirmCostDialog` | Shows estimate before LLM-backed runs |

## 5. States

Every data view handles these states:

- **Loading:** skeleton rows. Readings stream progress ("Parashari pass… KP pass…").
- **Empty:** explanation + primary action.
- **Error:** problem+json `title` and `detail` in the current language, the error code, and a retry action where retryable.
- **Partial:** e.g. a reading where one tradition pass failed. Show what exists and mark what is missing.
- **Stale:** a chart computed with an older engine/profile version → banner offering to recompute (creates a new chart).
- **Warning:** boundary/time-zone/OCR/provisional warnings inline.

## 6. Language and typography

- All strings live in `apps/web/messages/{en,hi}.json`. Missing keys fail CI.
- Fonts: Noto Sans (Latin) and Noto Sans Devanagari, self-hosted (no CDN calls).
- `lang` attribute set per element for mixed-language content (`hi`, `sa`, `sa-Latn` for IAST).
- Numerals: Western digits by default in both languages; Devanagari digits optional (setting).
- Dates: locale-formatted display; ISO in data.
- Sanskrit terms: Devanagari primary in Hindi UI, IAST primary in English UI, the other on hover.
- Hindi translations of UI strings and glossary need human review before release (tracked in implementation plan).

## 7. Accessibility (target WCAG 2.2 AA)

- Full keyboard navigation; visible focus; skip links.
- Colour contrast ≥ 4.5:1 for text. Tradition and status are never encoded by colour alone.
- Every chart diagram and bar chart has a data table equivalent.
- Live regions announce streaming reading progress.
- Respect `prefers-reduced-motion` and `prefers-color-scheme` (light/dark themes).
- Minimum target size 24×24 px.
- Automated checks with axe in Playwright tests (see [testing.md](testing.md)).

## 8. Design references

- No external brand or visual references supplied yet. **Owner to add** (screenshots of tools they like or dislike).
- Chart diagram conventions follow standard North-Indian (diamond, fixed houses) and South-Indian (fixed signs) layouts.
- Visual tone: neutral research tool, similar in density to data-analysis dashboards. Tradition colours (PROPOSED): Parashari = indigo, KP = teal, Jaimini = amber, each with a distinct icon.
