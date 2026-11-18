# User Stories — Jyotish Research Platform

> Status: DRAFT v0.3 (2026-11-17, post-review corrections). Persona for release 1: **the Owner**, a single local user acting as researcher, source approver, and evaluator. Reads English and Hindi. Not a programmer or Jyotish specialist, and not expected to validate Jyotish rules as a specialist (verification roles: [testing.md](testing.md) §7).
> Feature IDs (F1–F10) refer to [prd.md](prd.md). Story IDs are stable; reference them in commits and tests.

Acceptance criteria use Given / When / Then where useful. "Recorded" means persisted with the chart, reading, or run and visible in the UI.

---

## Epic E1 — Birth data & charts (F1)

### US-101 Enter birth data

As the Owner, I want to enter a birth date, local time, and place so that I can calculate a chart.

- Place search works offline and shows matching places with country, region, lat/lon, and time zone.
- I can enter coordinates manually if the place is not found.
- I can record time uncertainty (± minutes) and its source (certificate / hospital record / family recall / rectified / unknown).
- The original input is saved exactly as entered and is never changed by later normalization.
- Invalid dates (e.g. 31 Feb) are rejected with a message in the current UI language.

### US-102 See and override time-zone resolution

As the Owner, I want to see the UTC offset and DST the system applied so that I can catch historical time-zone errors.

- The chart shows: time-zone name, UTC offset, DST yes/no, tzdata version, resulting UTC time.
- Given a local time that falls in a DST gap, the system flags it as nonexistent and asks me to choose.
- Given a local time that occurs twice (DST fall-back), the system flags it as ambiguous and asks me to choose.
- Given an Indian birth before 1955-01-01, a warning explains that local time standards varied and offers manual offset entry.
- A manual override is recorded with a reason.

### US-103 Calculate a chart with an explicit profile

As the Owner, I want each chart to use a named calculation profile so that I always know which conventions were applied.

- Parashari and KP show their single Release 1 profile (`parashari-lahiri`, `kp-krishnamurti`) with a PROPOSED-convention badge.
- Jaimini has **no preselected profile**. I must choose between two separate calculation profiles, `jaimini-lahiri-7k` (seven karakas) and `jaimini-lahiri-8k` (eight karakas incl. Rahu), before the chart can be created (owner decision on Q-006: no default).
- The screen states that the karaka choice does not select a Chara Dasha method.
- The chart header shows ayanamsha (name + value), node type, house system, profile version, engine version, ephemeris version.
- Recalculating with a different profile creates a new chart and does not overwrite the old one.

### US-104 View the chart

As the Owner, I want to view the chart as a North-Indian or South-Indian diagram and as a table.

- Table columns: body, sidereal sign, degree (D°M'S"), nakshatra, pada, retrograde, speed.
- Diagram style preference is remembered.
- Every diagram has an equivalent accessible table.

### US-105 Boundary warnings

As the Owner, I want warnings when a value sits close to a boundary so that I know which conclusions are fragile.

- Warning shown when the lagna, a planet, or a KP cusp lies within the configured threshold of a sign, nakshatra, pada, or sub boundary.
- Each warning states how many minutes of birth-time change would cross the boundary.

### US-106 Birth-time sensitivity report

As the Owner, I want to see what changes within the stated time uncertainty.

- Given ±N minutes, the report lists facts that differ at −N and +N (lagna, nakshatra pada, D9 lagna, KP cusp sub-lords, karaka order, dasha balance).
- Facts that do not change are summarized as stable.

---

## Epic E2 — Parashari (F2)

### US-201 Lordships, dignity, aspects

As the Owner, I want Parashari house lordships, planetary dignities, and graha drishti so that I can see the basic chart structure.

- Each output item links to its rule ID(s).
- Special aspects of Mars (4, 8), Jupiter (5, 9), Saturn (3, 10) are shown per the selected rule records.

### US-202 Yogas

As the Owner, I want detected yogas with their conditions so that I can see why each yoga is present or absent.

- Each detected yoga shows: rule ID, conditions met, exceptions/cancellations checked, source citation.
- Yogas whose rule status is PROVISIONAL or CONFLICTING_SOURCES are labelled as such.
- A "near-miss" view lists yogas that fail exactly one condition (optional toggle).

### US-203 Shadbala

As the Owner, I want Shadbala with every component so that I can verify strength figures.

- Shows Sthana, Dig, Kala, Cheshta, Naisargika, Drik bala, total in rupas, and required minimum.
- Convention choices used in the computation are listed.

### US-204 Divisional charts

As the Owner, I want D1, D2, D3, D7, D9, D10, D12, D30.

- The varga selector lists only these eight charts (D-009); no other varga is offered in Release 1.
- Each varga's calculation method is named (e.g. Parashari D2 Hora).
- Varga positions are shown as diagram and table.

### US-205 Vimshottari Dasha

As the Owner, I want Vimshottari Dasha periods so that I can study timing.

- Shows balance of dasha at birth, Mahadasha / Antardasha / Pratyantardasha with start and end dates.
- Year-length convention is shown.
- Current period is highlighted.

---

## Epic E3 — KP (F3)

### US-301 Star, sub, sub-sub lords

As the Owner, I want star lord, sub lord, and sub-sub lord for every planet and cusp.

- Values agree with VERIFIED golden cases.
- A position exactly on a sub boundary is assigned per the documented rule (start-inclusive, D-006) and flagged.

### US-302 Cusps and cuspal sub-lords

As the Owner, I want Placidus cusps with their sub-lords.

- Given a birthplace above the latitude where Placidus is undefined, the system returns a clear error with alternatives, not wrong numbers.

### US-303 Significators

As the Owner, I want house significators by the KP four-level scheme so that I can follow a KP analysis.

- Shows levels 1–4 per house and the derivation path for each significator.
- No Parashari aspect or house-lord logic is used.

### US-304 Ruling planets

As the Owner, I want ruling planets for a chosen moment and place.

- Shows day lord, lagna sign lord, lagna star lord, lagna sub lord, Moon sign lord, Moon star lord, Moon sub lord (per selected rule record).
- Defaults to "now" at my configured location.

---

## Epic E4 — Jaimini (F4)

### US-401 Chara Karakas

As the Owner, I want Chara Karakas under the Jaimini profile I explicitly chose.

- The chart shows which profile it uses: seven karakas (`jaimini-lahiri-7k`) or eight karakas incl. Rahu (`jaimini-lahiri-8k`), plus the Rahu degree method for 8k.
- Comparing the two schemes means two charts, one per profile. There is no in-place switch.
- Ties (equal degrees within the configured precision) are flagged with the tie-break rule used.

### US-402 Rashi Drishti and Argala

As the Owner, I want sign aspects and Argala/Virodhargala.

- Rashi Drishti is shown separately from, and never merged with, Parashari graha drishti.
- Each Argala shows the obstructing positions and the net result per the rule record.

### US-403 Chara Dasha (gated: under research)

As the Owner, I want K.N. Rao Chara Dasha periods once the method has been specified and verified.

**Until the D-008 gates are passed (current state):**

- The Chara Dasha tab shows "Under research: not available" with a link to D-008 and its open questions (Q-007, Q-008, Q-009, Q-017).
- No periods or dates are calculated.
- No other Chara Dasha variant and no general-knowledge method is shown as a substitute.

**After the D-008 availability gate is passed:**

- The method name, exact edition, and source are shown.
- Sign periods and sub-periods are shown with dates.
- The karaka scheme used, if any, is shown as documented in the source (Q-007). It is never assumed to be eight karakas.

---

## Epic E5 — Readings (F5)

### US-501 Single-tradition reading

As the Owner, I want a reading using only one tradition so that I can study that system on its own.

- The model receives only that tradition's facts, rules, and passages (verified by test).
- Every claim shows a tradition badge, a basis label, and citations where available.

### US-502 Comparative reading

As the Owner, I want the three traditions side by side on a topic (e.g. career).

- Three columns plus a summary marking agreement, disagreement, and silence.
- Disagreement is shown, never smoothed over.

### US-503 Combined reading

As the Owner, I want an optional synthesis that still attributes each point.

- Each synthesized point lists the originating claims and their traditions.
- The three individual readings remain accessible from the combined view.

### US-504 Reading in Hindi

As the Owner, I want any reading in Hindi.

- Sanskrit terms use the project glossary (Devanagari + IAST on hover).
- Citations, rule IDs, and fact links work the same as in English.

### US-505 Drill down from a claim

As the Owner, I want to click a claim and see the underlying facts, rule records, and source passages.

- Reaches the source passage in ≤ 2 clicks.
- If the passage's OCR is unreviewed, this is shown.

### US-506 Honest uncertainty

As the Owner, I want the reading to say when evidence is missing or conflicting.

- Given a question the rules do not cover, the reading says so instead of guessing.
- Claims built on PROVISIONAL or CONFLICTING_SOURCES rules are labelled.

### US-507 Reading provenance

As the Owner, I want each reading to record how it was produced.

- Recorded and visible on the reading:
  - runtime provider and the exact model ID returned by the provider;
  - model parameters; prompt versions with content hashes;
  - minimiser version; app git commit; retrieved rule and citation IDs; timestamp.
- Visible as inherited from each chart: chart ID, profile key/version/hash, engine version, ephemeris version, tzdata version (data-model §5.2).

---

## Epic E6 — Library (F6)

### US-601 Import a source

As the Owner, I want to add a book (PDF/scan) with its metadata.

- Required: title, tradition(s), language. Optional: author, edition, publisher, year, translator, commentator, rights.
- File checksum (SHA-256) is computed; duplicates are detected.
- The original file is stored unchanged outside the git repository.

### US-602 Extract and review text

As the Owner, I want text extracted with page mapping and a review status per page.

- Embedded text is used when available; otherwise OCR (eng/hin/san).
- Page view shows the image and extracted text side by side; I can correct the text and mark the page REVIEWED.

### US-603 Search the library

As the Owner, I want to search by words or meaning in English, Hindi, Sanskrit (Devanagari or IAST).

- Filters: tradition, source, language, review status.
- Results show source, chapter/verse/page, and a snippet.

---

## Epic E7 — Rules (F7)

### US-701 Browse rules

As the Owner, I want to browse rule records by tradition and topic.

- Shows status, sources, conditions, exceptions, alternatives.
- Shows which engine functions and tests reference the rule.

### US-702 Review a drafted rule

As the Owner, I want to check that an AI-drafted rule matches its cited source, and approve or reject the source and evidence.

- Status changes are recorded as `rule_review` entries with actor, review type, date, and note.
- A rule cannot become VERIFIED without at least one citation to a REVIEWED passage and my SOURCE_APPROVAL.
- The screen makes clear that my approval confirms the source and evidence. It is not a specialist validation of the Jyotish rule.
- Independent validation is shown only if a review by an independent reviewer or an independent calculation has been recorded.

---

## Epic E8 — Golden dataset & evaluation (F8)

### US-801 Manage golden cases

As the Owner, I want to view and review golden cases by collection and status.

- Cases have ID, dataset version, tradition, topic, inputs, profile, expected outputs, rule IDs, evidence, ambiguities, prohibited claims, status, history.
- Only VERIFIED cases enter the primary benchmark.

### US-802 Freeze a dataset version

As the Owner, I want to freeze the dataset so that benchmarks are comparable.

- Freezing records version, date, content hash, and case list.
- A frozen version cannot be edited; changes go into a new version.

### US-803 Run an evaluation

As the Owner, I want to run selected suites against a chosen runtime model and prompt version, optionally scored by a judge model.

- Runtime model and judge model are chosen separately, and only verified model IDs can be selected.
- I see an estimated cost before an LLM-backed run starts and must confirm.
- Run metadata from plan §12 is recorded, with runtime and judge configuration kept separate (data-model §6.3). The run is marked self-judged when both are the same model.
- The report records the spot-check sample: method, eligible count, sample size, selected case IDs (testing.md §6.4).

### US-804 Read an evaluation report

As the Owner, I want results by category with individual failures.

- No single global score; per-suite and per-tradition pass rates.
- Diff against a chosen baseline: new failures, fixed cases, unchanged.
- Each failed case shows expected vs actual.

### US-805 Approve a model migration

As the Owner, I want to approve or reject a candidate model against thresholds.

- Approval is blocked if any category is below threshold, unless I record an explicit override with a reason.
- The previous production baseline is retained and can be restored by configuration.

---

## Epic E9 — Settings & language (F9)

### US-901 Switch UI language

As the Owner, I want to switch the whole UI between English and Hindi.

- All UI strings come from translation files; no hard-coded strings.
- The chosen language persists.

### US-902 Manage calculation profiles

As the Owner, I want to view and clone profiles.

- Editing a profile creates a new version; charts keep their original profile version.

### US-903 Configure AI providers

As the Owner, I want to set API keys and model IDs.

- Keys are stored in `.env` / secrets, never shown in full in the UI.
- Runtime model and evaluation judge model are configured separately.
- A "verify" action checks that the model ID exists with the provider. The official-catalogue check (date, source, exact ID) is recorded in the decisions.md model register before the model is activated.
- An empty model ID is allowed; AI features stay disabled until a verified ID is set.

---

## Epic E10 — Data management (F10)

### US-1001 Export

As the Owner, I want to export a chart or reading as JSON and as a printable view.

### US-1002 Delete

As the Owner, I want to delete a birth record and everything derived from it.

- Deletion removes charts, readings, and cached results for that record, after confirmation.

### US-1003 Backup and restore

As the Owner, I want a one-command backup and restore of my data and library.

- See [deployment.md](deployment.md) §6.
