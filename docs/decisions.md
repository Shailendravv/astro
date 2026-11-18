# Decisions & Changelog — Jyotish Research Platform

> Lightweight ADR log. Each entry: context → decision → alternatives → consequences → status.
> **Statuses:** `ACCEPTED` (agreed by owner), `PROPOSED` (default suggested by Claude Code, awaiting owner confirmation; do not treat as final), `OPEN` (no default yet), `SUPERSEDED`.
> Plan §17 rule: *do not silently assume defaults*. Every PROPOSED convention must be confirmed by the owner, and tests must exist for whichever option is chosen.
> **Every PROPOSED entry states:** Proposal · Alternatives · Verification required · Open questions (→ §Open questions).
> **Changing a decision:** an ACCEPTED decision is changed only by a new entry that supersedes it. A PROPOSED entry may be revised in place, but each revision adds a **History** line and a changelog row. Nothing is deleted.
> **Terminology (added 2026-11-17, documentation correction; changes no decision):** "Opus" and "Opus 5.5" in this log mean **the configured Anthropic Opus model**. Its exact API model ID has **not** been verified against Anthropic's official model catalogue (Q-016). Model IDs are configuration values only. Three model roles are kept distinct: the **runtime model** (generates readings), the **evaluation judge model** (scores Track I criteria), and the **research/review model** (drafts or reviews rules and golden cases, recorded per record in `drafted_by` / `reviewed_by`). The same model may fill more than one role; when it is both runtime and judge, the run is *self-judged* (D-022).
> **Verification roles (added 2026-11-17, documentation correction):** Claude Code finds sources and drafts PROVISIONAL records and tests; automated tests check that code reproduces documented examples (they do not prove a Jyotish rule is correct); independent reviewers or calculations, **where available and recorded**, check interpretation; the owner approves decisions, source use, and evidence, and is **not** represented as a qualified Jyotish expert. Full text: [testing.md](testing.md) §7.

## Model ID verification register

Exact model IDs are recorded here only after checking the provider's **official** model catalogue or API documentation. None of these items blocks M1. **Update 2026-11-18 (owner decision, D-030):** no Anthropic model is used by the product. The rows below keep the original Anthropic entries for history and show their new state.

| Role | Provider | Exact model ID | Verified on | Official source checked | Status |
|---|---|---|---|---|---|
| Runtime model, Stage A | Anthropic (configured Opus model) | — | — | — | NOT USED: withdrawn by owner decision (D-030; Q-016 withdrawn) |
| Evaluation judge model | Anthropic (configured Opus model) | — | — | — | NOT USED: Anthropic excluded (D-030). Judge model is now an open question (Q-018) |
| Runtime model (all stages) | Groq (Qwen) | `qwen/qwen3.8-27b` | 2026-11-18 | https://console.groq.com/docs/model/qwen/qwen3.8-27b (also https://console.groq.com/docs/models, https://console.groq.com/docs/deprecations, https://console.groq.com/docs/your-data) | ID **provided by the owner and found in Groq's official catalogue**. Catalogue status is **Preview** (see D-012 and Q-019). Not yet exercised by any call. **Owner accepted it on 2026-11-18 as the initial experimental runtime, subject to its Preview status and limitations** (Q-019, partly answered) |
| Evaluation judge model | Groq (Qwen) | `qwen/qwen3.8-27b` | 2026-11-18 | same pages as the runtime row | **Proposed by the owner on 2026-11-18 (Q-018).** Same provider and ID as the runtime, so **every run is self-judged** (D-022). Recorded separately from the runtime in every run (`EVAL_JUDGE_*`). Not yet exercised by any call |
| Research/review model | Claude Code (the coding tool, not an app setting) | n/a | n/a | n/a | Recorded per record as `{actor: CLAUDE_CODE}`. No Anthropic API call is made by the app (D-030) |

## Index

| ID | Topic | Status | Plan §17 item |
|---|---|---|---|
| D-001 | Deployment target: local single-user first | ACCEPTED | 1 |
| D-002 | Languages: English + Hindi | ACCEPTED | 10 |
| D-003 | Ayanamsha policy & separate tradition profiles | PROPOSED (rev. 2) | 2 |
| D-004 | Node convention (configurable mean/true) | PROPOSED (rev. 2) | 3 |
| D-005 | House / cusp systems per tradition | PROPOSED (rev. 2) | 4 |
| D-006 | KP sub-division precision & boundaries | PROPOSED | 5 |
| D-007 | Chara Karaka schemes: separate 7- and 8-karaka profiles | PROPOSED (rev. 2) | 6 |
| D-008 | Initial Jaimini dasha: K.N. Rao Chara Dasha from the exact publication | PROPOSED (rev. 3) | 7 |
| D-009 | Initial vargas & Parashari feature set | PROPOSED | 8 |
| D-010 | Birth-time uncertainty | PROPOSED | 9 |
| D-011 | Book collection, editions, rights + recommended reference list | OPEN (list PROPOSED, rev. 2) | 11 |
| D-012 | Groq model identifier | OPEN → ID RECORDED 2026-11-18 (owner-provided, catalogue-checked; Preview status, see Q-019) | 12 |
| D-013 | Ephemeris library & licensing | PROPOSED | 13 |
| D-014 | Hardware / OS / dev environment | PROPOSED | 14 |
| D-015 | Geocoding source | PROPOSED | — |
| D-016 | Historical time-zone source | PROPOSED | — |
| D-017 | Database & library search | PROPOSED | — |
| D-018 | Rules & golden cases stored as YAML in git | PROPOSED | — |
| D-019 | Python version | PROPOSED | — |
| D-020 | OCR approach | PROPOSED | — |
| D-021 | Enforce tradition isolation with import-linter | PROPOSED | — |
| D-022 | Deterministic vs interpretation evaluation; Opus as deliberate judge | ACCEPTED (rev. 2, 2026-11-17) | — |
| D-023 | All reading types built before initial Opus evaluation | ACCEPTED (rev. 2, 2026-11-17) | — |
| D-024 | Git hosting & CI | PROPOSED | — |
| D-025 | Vimshottari Dasha year length | PROPOSED (rev. 2) | — |
| D-026 | Accepted principles from the project plan | ACCEPTED | — |
| D-027 | AI-provider payloads are personal data; minimisation | ACCEPTED (principle) / PROPOSED (precision values) | — |
| D-028 | Progressive evaluation framework | ACCEPTED (2026-11-17) | — |
| D-029 | Hindi evaluation suites | ACCEPTED (2026-11-17) | — |
| D-030 | No Anthropic model in the product; Groq Qwen is the only runtime provider | ACCEPTED (owner, 2026-11-18); supersedes the Anthropic-specific parts of D-022, D-023 | — |
| D-031 | Rule knowledge base schema, lifecycle, approval audit and retrieval gate | PROPOSED (requirements owner-directed 2026-11-18; design details awaiting owner acceptance) | — |

---

## D-001 Deployment target: local single-user first — ACCEPTED (2026-11-17)

- **Context:** Plan §17.1 left the target open. Users and hosting drive auth, security, and ops scope.
- **Decision:** Release 1 is for the owner only, running locally via Docker Compose on their machine. No accounts.
- **Alternatives:** private multi-user web app; public SaaS.
- **Consequences:** No auth in R1; network isolation instead. API kept stateless so auth can be added later. DPDP/GDPR obligations re-assessed before any change. Swiss Ephemeris AGPL is not triggered.

## D-002 Languages: English + Hindi — ACCEPTED (2026-11-17)

- **Decision:** UI and readings in English and Hindi from release 1. Sanskrit terms in IAST and Devanagari via a shared glossary.
- **Consequences:** i18n framework from day one; Hindi variants of interpretation/integration/adversarial golden cases; Hindi UI and glossary need human review; evaluation reports split by language. (Evaluation detail: D-029.)

## D-003 Ayanamsha policy & separate tradition profiles — PROPOSED (rev. 2)

- **Proposal:**
  - Three **separate, independently versioned** profile families. A change to one never changes another:
    - `parashari-lahiri`: Lahiri / Chitrapaksha.
    - `jaimini-lahiri-7k`, `jaimini-lahiri-8k`: Lahiri / Chitrapaksha (two Jaimini profiles, see D-007).
    - `kp-krishnamurti`: KP-specific Krishnamurti ayanamsha (Swiss Ephemeris `SE_SIDM_KRISHNAMURTI`).
  - Parashari and Jaimini profiles both use Lahiri but **do not share a profile object**.
  - Swiss Ephemeris Lahiri constant: `SE_SIDM_LAHIRI`, pending Q-001.
- **Alternatives:** Lahiri sub-variants (`LAHIRI_1940`, `LAHIRI_VP285`, `LAHIRI_ICRC`); True Chitra; Raman; Yukteshwar. For KP: KP "New" / `KRISHNAMURTI_VP291`. All may be added as further profile versions, never as silent switches.
- **Verification required:** compare the computed Lahiri ayanamsha for sample dates against the *Indian Astronomical Ephemeris* (Positional Astronomy Centre) values; compare the KP ayanamsha against the tables or worked examples in KP Reader I or a KP ephemeris (D-011). Golden cases for each profile; test that the same input under different profiles produces the documented difference.
- **Open questions:** Q-001, Q-002.
- **History:** rev. 1 (2026-11-17) proposed generic `parashari-default` / `kp-default` / `jaimini-default` profiles. rev. 2 (2026-11-17, architecture review) splits Parashari and Jaimini Lahiri profiles and renames the profiles after their convention.

## D-004 Node convention (configurable) — PROPOSED (rev. 2)

- **Proposal:** `node: MEAN | TRUE` is a **required setting in every profile**. No engine has a built-in node default. PROPOSED initial value: `MEAN` in all profiles.
- **Alternatives:** `TRUE` node in any or all profiles.
- **Why it matters:** mean and true node differ by up to roughly 1.5°, enough to change Rahu/Ketu nakshatra, pada, KP sub-lord, and (8-karaka) Jaimini karaka order.
- **Verification required:** tests run node-dependent calculations under **both** settings; property test that Rahu–Ketu separation is exactly 180° for both; golden cases with both values where sources give examples.
- **Open questions:** Q-003.
- **History:** rev. 1 proposed mean node as default with true node "available per profile". rev. 2 makes the setting mandatory and explicitly tested both ways.

## D-005 House / cusp systems — PROPOSED (rev. 2)

- **Proposal:** Parashari: **whole sign** houses, Bhava Chalit (Sripati) as an optional view. KP: **Placidus** cusps (proposed KP house system). Jaimini: **whole sign** (sign-based).
- **Alternatives:** Parashari with Sripati bhavas as primary; KP with another quadrant system (not standard KP practice, documented only if a source requires it).
- **Verification required:** Placidus cusps compared against Swiss Ephemeris reference values and KP worked examples (D-011); high-latitude cases return `HOUSE_SYSTEM_UNDEFINED`, not a silent fallback.
- **Open questions:** Q-004.
- **History:** rev. 2 adds alternatives, verification, and open question.

## D-006 KP sub-division precision & boundaries — PROPOSED

- **Proposal:** Generate the 249-sub table from Vimshottari proportions using exact rational arithmetic (`Fraction`) in arc-seconds. Boundaries are **start-inclusive** (a longitude exactly on a boundary belongs to the following sub). Compare positions at full float precision converted to milli-arcseconds. Warn when within `boundary_warning_arcmin` (default 2′) and report minutes of birth time to cross.
- **Alternatives:** rounding to the arc-second before lookup (some software); end-inclusive.
- **Verification required:** generated table matches the KP sub table in the owner's KP reference (D-011) entry by entry; boundary tests on both sides of every sub boundary.
- **Open questions:** Q-005.

## D-007 Chara Karaka schemes — PROPOSED (rev. 2)

- **Proposal:**
  - Two **separate calculation profiles**: `jaimini-lahiri-7k` (seven karakas, Sun–Saturn) and `jaimini-lahiri-8k` (eight karakas including Rahu, Rahu's degree counted as 30° − degree in sign).
  - `karaka_scheme` is **independent of** `jaimini_dasha_method`. Choosing a Chara Dasha method does **not** select a karaka scheme, and the 8-karaka scheme is **not** assumed to be part of K.N. Rao's Chara Dasha method (see D-008, Q-007).
  - Ties (equal degrees at the configured precision): flagged and resolved only by a documented rule record per scheme; never silently.
  - Which profile is preselected in the UI is unresolved (Q-006). Until it is answered, the UI asks the user to choose.
- **Alternatives:** one profile with a variant switch (rejected: it hides the convention inside a profile); 8-karaka only; 7-karaka only.
- **Verification required:** rule records citing the source passages for each scheme (e.g. BPHS chapter on Chara Karakas for the 8-karaka view; Jaimini Sutra commentaries for the 7-karaka view; locators recorded once the library is ingested); golden cases for both schemes incl. ties and Rahu edge cases.
- **Open questions:** Q-006, Q-007.
- **History:** rev. 1 proposed 8-karaka as default with 7-karaka as a variant. rev. 2 (architecture review) makes them separate profiles with no assumed default and decouples them from the dasha method.
- **History:** 2026-11-18 owner decision on **Q-006**: there is **no default Jaimini karaka profile**. The user must explicitly select either `jaimini-lahiri-7k` or `jaimini-lahiri-8k`; nothing is preselected in the UI, API, settings, or tests. This settles only the "which profile is preselected" question. The two-profile structure, the ties rule, and the verification requirements above stay PROPOSED, and Q-007 stays open.

## D-008 Initial Jaimini dasha: K.N. Rao Chara Dasha — PROPOSED (rev. 3)

- **Proposal:** Release 1 implements Chara Dasha **as specified in K.N. Rao, *Predicting Through Jaimini's Chara Dasha*** (publisher, edition, and year to be recorded from the owner's copy, Q-008), method ID `CHARA_KNRAO_<edition-key>`.
- **Specification process (blocking):** before any code, every calculation step becomes a Jaimini rule record citing chapter/page of that edition. Nothing is filled in from general knowledge or other Chara Dasha variants. Steps that need a cited rule (Q-009):
  1. Starting sign of the dasha sequence.
  2. Direction rule (forward or backward through the zodiac) and how it is determined.
  3. Mahadasha length: counting method from sign to its lord, treatment of a lord in its own sign, any exaltation/debilitation adjustments.
  4. Signs with two lords (Scorpio, Aquarius): which lord is used and the strength/tie-break rules.
  5. Antardasha order and lengths.
  6. Whether and how a second cycle is computed.
  7. Year length used for converting periods to dates.
  8. Whether Chara Karakas (and which scheme) enter the calculation at all, or only the interpretation (Q-007).
- **Alternatives:** other Chara Dasha variants (e.g. per Sanjay Rath, Iranganti Rangacharya, or other commentators) and Narayana Dasha. Each gets its own method ID later and is never merged with `CHARA_KNRAO`.
- **Verification required:** reproduce every worked example in the book exactly (golden cases cite page numbers); cross-check against at least one independent software implementation that claims to follow K.N. Rao's method (record name, version, settings); owner approves the source and evidence of each rule record (source approval; see rev. 3 below). Implementation stays blocked until the step rules are VERIFIED.
- **Responsibilities and gates (rev. 3):** roles as in [testing.md](testing.md) §7.
  - *Claude Code* records the exact edition (Q-008), drafts one PROVISIONAL rule record per step with chapter/page citations, and reports ambiguities or conflicts instead of resolving them.
  - *Owner* approves the edition, the source transcription, and the cited evidence for each step (source approval). This is what moves a step rule to VERIFIED (data-model §4.4). **Owner source approval is not independent expert validation of the Jyotish method**, and is not presented as such.
  - *Independent check:* an independent source, qualified reviewer, or independent implementation is recorded **only if one actually exists**. None is assumed or invented. Each rule records its `independent_validation` status.
  - *Automated tests* show that the code reproduces the book's worked examples. They do not prove the method is correct.
  - **Implementation gate (unchanged):** no Chara Dasha code until all eight step rules cite the exact edition and are VERIFIED.
  - **Availability gate (unchanged):** Chara Dasha is not offered as a usable feature (UI shows it as *under research*, API returns `METHOD_NOT_AVAILABLE`) until implementation exists **and** every item under *Verification required* above is complete, including the independent software cross-check.
  - Owner approval of documentation alone does not open either gate. If no independent implementation or reviewer can be found, the availability gate stays closed until the owner decides how to proceed (Q-017).
- **Open questions:** Q-007, Q-008, Q-009, Q-017.
- **History:** rev. 1 proposed "the method as published by K.N. Rao" without a specification process. rev. 2 requires the exact publication and a cited rule per calculation step.
- **History:** rev. 3 (2026-11-17, owner-approved documentation correction) adds the responsibilities-and-gates block: separates source approval from independent validation, makes the availability gate explicit, and adds Q-017. It also rewords "owner verifies the rule records" (rev. 2) as "owner approves the source and evidence of each rule record". The edition requirement, the eight-step specification, and the implementation block are unchanged. Status stays PROPOSED.
- **History:** 2026-11-18 owner decision on **Q-017** (no text above is changed; this tightens how the availability gate is read). Chara Dasha stays **unavailable in the initial release** (UI "under research", API `METHOD_NOT_AVAILABLE`) **unless both** of these exist: (1) a **source-approved specification** (all eight step rules VERIFIED against the exact edition) and (2) an **independent calculation check** (an independent implementation or calculation, recorded with name/version/settings). Owner approval of documents alone does not open the gate, and no weaker evidence is accepted. Other Jaimini work (karakas, Rashi Drishti, Argala, Karakamsha) continues under its own verification gates. Status stays PROPOSED; Q-007, Q-008, Q-009 stay open.

## D-009 Initial vargas & Parashari features — PROPOSED

- **Proposal:** Vargas tranche 1: **D1, D2, D3, D7, D9, D10, D12, D30** (covers Saptavarga for Shadbala plus D10). Parashari R1: lordships, dignity, graha drishti, ~20 well-attested yogas, Shadbala, Vimshottari (3 levels). Deferred: remaining Shodashavarga, Ashtakavarga, transits.
- **Alternatives:** full Shodashavarga in R1; fewer vargas.
- **Verification required:** each varga's division method cited to BPHS (or stated alternative); worked examples from Parashari references (D-011) as golden cases.

## D-010 Birth-time uncertainty — PROPOSED

- **Proposal:** Record ± minutes and time source. Provide boundary warnings and a sensitivity report at window edges. No automatic rectification in R1. Readings mention time-sensitive conclusions.
- **Alternatives:** rectification tools (deferred).
- **Verification required:** sensitivity tests on sandhi-lagna and near-sub-boundary cases ([testing.md](testing.md) §4).

## D-011 Book collection, editions, rights — OPEN (recommended list PROPOSED, rev. 2)

- **Status:** OPEN until the owner supplies the actual inventory (T2.1). The list below is a **recommendation** of standard references to acquire or check against. Claude Code has **not** verified any edition, publisher, or year. Every row must be completed from the physical/legal copy before ingestion.
- **Acquisition rule:** only lawfully obtained copies (purchased, owned, public domain, or licensed). No pirated PDFs.
- **Metadata recorded per source** (see [data-model.md](data-model.md) §4.1): title, author, translator/commentator, edition, publisher, year, language, ISBN (if any), file checksum, chapter/verse/page mapping, rights, rights-check notes, OCR review status.

### Copyright check procedure (per source)

1. Separate the **original text** (classical Sanskrit, generally public domain) from the **translation/commentary** (separately copyrighted).
2. For the translation/commentary: identify the translator's/commentator's death year. Under the Indian Copyright Act, literary works generally remain protected for 60 years from the beginning of the calendar year after the author's death. Record the year and the conclusion; if unknown, record `UNKNOWN` and treat as in copyright.
3. Record `rights` = `PUBLIC_DOMAIN` | `OWNED_COPY_PERSONAL_USE` | `LICENSED` | `UNKNOWN`.
4. In-copyright sources: personal research use only. Not committed to git, not redistributed, excerpts sent to AI providers capped ([security.md](security.md) §4).
5. Digital collections (GRETIL, Cologne dictionaries, etc.): check the licence of the **digital edition** separately from the underlying text.

### Recommended references (PROPOSED: all bibliographic details "to verify")

| Proposed source ID | Work | Translator / author of edition | Publisher (to verify) | Lang | Tradition | Purpose | Initial copyright assumption |
|---|---|---|---|---|---|---|---|
| SRC-BPHS-SANTHANAM | Brihat Parashara Hora Shastra | R. Santhanam (2 vols) | Ranjan Publications | sa/en | Parashari (+ Jaimini chapters) | Core Parashari rules, vargas, Shadbala, Vimshottari, karakas, argala | Translation in copyright |
| SRC-BPHS-GCSHARMA | Brihat Parashara Hora Shastra | Girish Chand Sharma (2 vols) | Sagar Publications | sa/en | Parashari | Second translation to expose translation differences | Translation in copyright |
| SRC-BPHS-HI | Brihat Parashara Hora Shastra (Hindi commentary) | Hindi commentator to identify (e.g. a Chaukhamba edition) | Chaukhamba (to verify) | sa/hi | Parashari | Hindi terminology and Hindi reading consistency | Check commentator's death year |
| SRC-PHALADEEPIKA | Phaladeepika (Mantreswara) | V. Subrahmanya Sastri, or G.S. Kapoor | to verify | sa/en | Parashari | Yogas, dignities, bhava results | Check translator's death year |
| SRC-SARAVALI | Saravali (Kalyana Varma) | R. Santhanam | Ranjan Publications | sa/en | Parashari | Yogas and planetary combinations | Translation in copyright |
| SRC-BRIHAT-JATAKA | Brihat Jataka (Varahamihira) | V. Subrahmanya Sastri, or B. Suryanarain Rao | to verify | sa/en | Parashari (foundational) | Foundational definitions | Older translations may be public domain; verify |
| SRC-JATAKA-PARIJATA | Jataka Parijata (Vaidyanatha Dikshita) | V. Subrahmanya Sastri | to verify | sa/en | Parashari | Yogas, vargas | Check translator's death year |
| SRC-RAMAN-BALAS | Graha and Bhava Balas | B.V. Raman | to verify | en | Parashari | Shadbala calculation reference with worked examples | In copyright |
| SRC-RAMAN-300 | Three Hundred Important Combinations | B.V. Raman | to verify | en | Parashari | Yoga definitions with examples | In copyright |
| SRC-KP-READER-1…6 | KP Readers I–VI (I Casting the Horoscope; II Fundamental Principles; III Predictive Stellar Astrology; IV Marriage, Married Life & Children; V Transit; VI Horary) | K.S. Krishnamurti | Krishnamurti Publications (to verify) | en | KP | Primary KP source: ayanamsha, sub table, cusps, significators, ruling planets | In copyright |
| SRC-KP-EPHEMERIS | KP ephemeris / table of houses with KP ayanamsha | to identify | to verify | en | KP | Verification of KP ayanamsha and cusps (D-003, D-005) | Check |
| SRC-JAIMINI-RATH | Jaimini Maharishi's Upadesa Sutras | Sanjay Rath | Sagar Publications (to verify) | sa/en | Jaimini | Sutras with commentary | Translation in copyright |
| SRC-JAIMINI-PSSASTRI | Jaimini Sutras | P.S. Sastri | Ranjan Publications (to verify) | sa/en | Jaimini | Alternative translation | Check |
| SRC-JAIMINI-IRANGANTI | Jaimini Sutramritam | Iranganti Rangacharya | Sagar Publications (to verify) | sa/en | Jaimini | Alternative commentary (different dasha views) | In copyright |
| SRC-JAIMINI-BSRAO | Jaimini Sutras | B. Suryanarain Rao | to verify | sa/en | Jaimini | Older translation | May be public domain; verify death year |
| SRC-KNRAO-CHARA | Predicting Through Jaimini's Chara Dasha | K.N. Rao | Vani Publications (to verify) | en | Jaimini | **Primary specification for D-008** | In copyright |
| SRC-MW-DICT | A Sanskrit-English Dictionary (1899) | M. Monier-Williams | Oxford (digital: Cologne Digital Sanskrit Dictionaries) | sa/en | Sanskrit | Terminology, glossary | Original public domain; check digital-edition licence |
| SRC-APTE-DICT | The Practical Sanskrit-English Dictionary | V.S. Apte | to verify (original late 19th c.) | sa/en | Sanskrit | Terminology cross-check | Original edition public domain; later revisions verify |
| SRC-IAST | IAST transliteration conventions (and ISO 15919 for comparison) | — | — | — | Sanskrit | Transliteration standard for the glossary | Conventions only; ISO text is paywalled |
| SRC-GRETIL | GRETIL Sanskrit e-texts (where Jyotish texts exist) | various | Göttingen (GRETIL) | sa | Sanskrit / all | Machine-readable Sanskrit originals to check OCR | Per-text licence check |
| SRC-IAE | Indian Astronomical Ephemeris | Positional Astronomy Centre, Kolkata | Govt. of India (to verify) | en | Shared | Lahiri ayanamsha verification (D-003) | Government publication; check terms |

- **Open questions:** Q-014, Q-015.
- **History:** rev. 1 recorded only the need for an inventory. rev. 2 (architecture review) adds the recommended list, metadata fields, and copyright check procedure.

## D-012 Groq model identifier — OPEN → ID RECORDED (2026-11-18)

- **Decision rule (ACCEPTED from plan §8):** do not hard-code. Verify exact ID and availability in Groq's official catalogue at Phase 11; record here with date, model ID, context window, structured-output support, data-retention policy.
- **Record, 2026-11-18** (owner supplied the ID; Claude Code checked it in Groq's official documentation, read directly from the pages listed in the model register):

| Item | Value as shown by Groq |
|---|---|
| Exact model ID | `qwen/qwen3.8-27b` (page title "Qwen/Qwen3.8-27B") |
| Catalogue status | **Preview**. Groq's models page says: "Preview models are intended for evaluation purposes only and should not be used in production environments as they may be discontinued at short notice." |
| Context window / max output | 131,072 tokens / 16,384 tokens |
| Capabilities listed | Tool Use, JSON Object Mode, JSON Schema Mode, Reasoning, Vision (input: text, images; output: text) |
| Documented settings | Thinking mode (`reasoning_effort="default"`, temperature 1.0, top_p 0.95, top_k 20) and instruct mode (`reasoning_effort="none"`, temperature 0.7, top_p 0.80, top_k 20, presence_penalty 1.5). `reasoning_format` may be `hidden` or `parsed`. Which mode the product uses is not decided (see Q-019) |
| Pricing shown | Input $0.80 per 1M tokens, output $4.00 per 1M tokens (re-check before any paid run) |
| Deprecation | No shutdown date listed for this ID. Its predecessor `qwen/qwen3.6-27b` has a shutdown date of 09/14/26 with this model as the recommended replacement, and `qwen/qwen3-32b` was shut down 07/17/26. Groq retires Qwen models quickly |
| Data retention (Groq "Your Data" page) | Inference requests are not retained by default. Inputs and outputs may be logged temporarily, for up to 30 days, only to troubleshoot reliability or investigate abuse. Zero Data Retention (ZDR) can be enabled in the Groq console "Data Controls". Retained data is stored in the United States (GCP) |

- **What this does not settle:** the model has **not been called**; JSON Schema Mode working for our claim schema is **untested** (check at T8.2); the Preview status and the retirement pattern are a risk the owner has not yet accepted (Q-019); ZDR is not yet confirmed as enabled on the owner's account (D-027, security.md §4 require recording retention settings before activation).
- **Rule kept:** the ID lives only in this register and in the owner's local `.env` (`RUNTIME_MODEL_ID`). It is never written into code, prompts, tests, or other docs.
- **History:** 2026-11-18 owner supplied `qwen/qwen3.8-27b` and stated the product will use no Anthropic model (D-030). Claude Code verified the ID against the official catalogue the same day. Status moves from OPEN to "ID recorded"; acceptance of Preview status is Q-019.
- **History:** 2026-11-18 (second owner message). The owner **accepted `qwen/qwen3.8-27b` as the initial experimental runtime, subject to its Preview status and limitations** (Q-019, partly answered). **Zero Data Retention is UNCONFIRMED**: the owner cannot currently say whether ZDR is enabled on their Groq account. It is not assumed to be enabled. Until the owner confirms, the data-handling precautions in [security.md](security.md) §4 "While ZDR is UNCONFIRMED" apply. No real (non-fake) model call is made until the owner approves the provider configuration and data-handling requirements (gate in security.md §4). The row "What this does not settle" above still holds for everything not named here (model not called, JSON Schema Mode untested, fallback policy and thinking/instruct mode not chosen).

## D-013 Ephemeris & licensing — PROPOSED

- **Proposal:** Swiss Ephemeris via `pyswisseph` under **AGPL-3.0** for local personal use (no distribution). Data files covering 1800–2399. Independent test reference: **Skyfield + JPL DE440/441**.
- **Alternatives:** Swiss Ephemeris professional licence; Skyfield-only implementation (would need own ayanamsha and house code).
- **Verification required:** astronomy suite ≤ 1″ vs JPL reference over sampled dates.
- **Consequences:** Any future distribution or hosted service requires either AGPL compliance (publish source) or a Swiss Ephemeris professional licence. Revisit with D-001.

## D-014 Hardware / OS / dev environment — PROPOSED

- **Observed:** Windows 11. **Proposal:** Docker Desktop with WSL2, Git for Windows, VS Code + Claude Code, Python via `uv`, Node LTS.
- **To confirm:** RAM/disk (local embeddings + Postgres + OCR need ~16 GB RAM recommended, ~20 GB disk excl. library).
- **History:** 2026-11-18 T1.1 observation (Claude Code, from the owner's machine; nothing else in this entry changes). Windows 11 Home; 15.8 GB RAM (right at the recommended 16 GB, so watch memory when local embeddings and OCR arrive in M2); D: has ~268 GB free, C: ~68 GB. Installed: Git 2.43.0, Docker 28.3.2 with Compose v2.39.1 (Docker Desktop **was not running** at the time of the check), Node v22.13.0 / npm 10.9.2, uv 0.11.19. System Python is 3.11.9, but uv provides CPython 3.12.13, which the project uses (D-019). WSL is installed. Status stays PROPOSED.

## D-015 Geocoding source — PROPOSED

- **Proposal:** Offline GeoNames (`cities500`) imported into Postgres; manual coordinates allowed. No birthplace sent to online geocoders. CC-BY attribution required.

## D-016 Historical time-zone source — PROPOSED

- **Proposal:** IANA tzdata via Python `zoneinfo` + `tzdata` package (version pinned and recorded). Manual offset override with reason. Warning for Indian births before 1955 and for LMT.

## D-017 Database & library search — PROPOSED

- **Proposal:** PostgreSQL 17 with FTS and `pgvector`. Embeddings from a **local** multilingual model (Hindi/Sanskrit capable; exact model chosen during M2 by a small retrieval test), so book text is not sent to an embedding API.
- **Alternatives:** hosted embedding API (better quality, but sends copyrighted text out); separate search engine (more ops).

## D-018 Rules & golden cases as YAML in git — PROPOSED

- **Proposal:** Rule records (`knowledge/rules/<tradition>/*.yaml`) and golden cases (`evaluation/datasets/<collection>/*.yaml`) are the source of truth in git; Postgres holds a rebuildable index.
- **Why:** diffable review history, easy for Claude Code to edit, reproducible dataset freezes via content hash.

## D-019 Python version — PROPOSED

- **Proposal:** Python 3.12 (broad wheel support incl. `pyswisseph`); upgrade when all deps support newer versions.

## D-020 OCR approach — PROPOSED

- **Proposal:** Prefer embedded text; otherwise Tesseract (`eng`, `hin`, `san`) locally. Mandatory human page review before passages can support VERIFIED rules. A cloud OCR option may be evaluated later for Devanagari quality, as a separate decision covering copyright and privacy.

## D-021 Tradition isolation via import-linter — PROPOSED

- **Proposal:** Encode "Parashari, KP, Jaimini engines must not import each other" and "engine must not import ai/apps/db" as import-linter contracts in CI. Makes plan §1 "Keep traditions distinct" mechanically enforced.

## D-022 Deterministic vs interpretation evaluation; Opus as deliberate judge — ACCEPTED (rev. 2, 2026-11-17)

- **Context:** Calculation outputs have right answers; open-ended readings do not. Plan §10.3 says Opus must not be the sole authority for cases it helped create.
- **Decision:**
  - **Track D: deterministic evaluation.** Numeric tolerance, exact categorical match, date match, rule assertions, citation-existence checks. No LLM involved. Runs in CI.
  - **Track I: interpretation scoring**, in three tiers:
    1. **Automatic checks first:** schema/validator, fact/rule/citation IDs exist, tradition attribution, prohibited claims, required facts referenced, output language/script, glossary terms.
    2. **Opus 5.5 as judge** for rubric criteria that automatic checks cannot decide. Used **only in deliberate evaluation runs:** initial testing (Stage A), future model migrations, and material prompt changes (plan §12). Never on ordinary user requests.
    3. **Owner spot-checks** of judge verdicts.
  - **Opus is never the sole authority** for accepting golden answers it generated or proposed. Such cases (`drafted_by` includes Opus) need owner approval **and** independent evidence (a reviewed source passage or an independent calculation) to become VERIFIED.
  - When Opus is both the runtime model and the judge (Stage A), results are labelled *self-judged*, and the owner spot-check rate rises (Q-012).
- **Consequences:** golden cases record `drafted_by` and `reviewed_by`; reports show Track D and Track I separately; Track I reports show which tier decided each criterion.
- **History:** rev. 1 (PROPOSED) "Opus as evaluation judge only". rev. 2 (owner-directed architecture review, 2026-11-17) adds the two-track separation and the governance rules, and changes status to ACCEPTED. Spot-check rates remain PROPOSED (Q-012).
- **History:** 2026-11-18 **partly superseded by D-030** (the original text above is kept unchanged). What is superseded: "Opus 5.5 as judge" and every statement that an Anthropic model is the judge or the Stage A runtime. What stays in force: the Track D / Track I separation, the three tiers, judge use only in deliberate runs, the self-judged flag, and the rule that **no model is the sole authority for accepting golden answers it drafted** (this now applies to any model, including Claude Code as drafting tool and Qwen). Which model acts as judge is open (Q-018).

## D-023 All reading types built before initial Opus evaluation — ACCEPTED (rev. 2, 2026-11-17)

- **Context:** Plan §15 puts integrated interpretation (Phase 12) after Opus validation (9) and Qwen stabilization (11). As written, comparative/combined readings would never be covered by the Opus baseline or the Qwen benchmark, and Stage A "run the initial system with Opus" needs readings to exist.
- **Decision:** Individual **Parashari, KP, and Jaimini readings, comparative readings, and optional combined readings** (en + hi) are all implemented in Phase 9, **before** the initial Opus 5.5 evaluation (Phase 10). Then Qwen integration (11), Qwen stabilization (12), release (13). See [implementation-plan.md](implementation-plan.md) §2.
- **History:** rev. 1 PROPOSED the reorder. rev. 2 (owner-directed architecture review, 2026-11-17) accepts it and lists the reading types explicitly.
- **History:** 2026-11-18 **partly superseded by D-030**. The ordering rule is unchanged: all reading types are built before the first full evaluation. What changes is the wording "initial Opus evaluation": the first full evaluation runs with the Groq Qwen runtime model (D-012), and the judge is decided under Q-018.

## D-024 Git hosting & CI — PROPOSED

- **Proposal:** Private GitHub repository + GitHub Actions. LLM evaluation never runs in CI.

## D-025 Vimshottari Dasha year length — PROPOSED (rev. 2)

- **Context:** Not listed in plan §17, but every Vimshottari date depends on it.
- **Proposal:** Initial default **365.25 days** per dasha year, stored as `dasha_year_days` in the Parashari profile (and in any KP profile that computes Vimshottari). Configurable; never hard-coded in the engine.
- **Alternatives:** 365.2422 (tropical year), ≈365.2564 (sidereal year), 360 (savana year), or a source-specified value.
- **Verification required (tests):**
  - Property: sum of Mahadashas = 120 × `dasha_year_days` days; Antardashas sum to their Mahadasha.
  - Golden cases computed under each supported value, showing the expected date shifts.
  - Test that changing only `dasha_year_days` changes only dasha dates.
  - Cross-check against worked examples in the Parashari references (D-011) and one reference program whose year-length setting is documented.
- **Scope note:** Jaimini Chara Dasha year length is a separate question (D-008 step 7).
- **Open questions:** Q-010.
- **History:** rev. 1 proposed 365.25 with alternatives. rev. 2 adds configurability, test requirements, and verification.

## D-026 Principles accepted from the project plan — ACCEPTED (2026-11-17)

Source before rule; traditions kept distinct; calculation separate from interpretation (no LLM calculations); conventions explicit; uncertainty recorded; reproducibility (versions recorded); no unsupported claims; evaluation deliberate, not continuous; provider adapter; model IDs not hard-coded; Opus for initial validation and migrations, Groq Qwen as intended runtime.

## D-027 AI-provider payloads are personal data; minimisation — ACCEPTED (principle, 2026-11-17) / PROPOSED (values)

- **Context:** Names, birthplaces, and birth date/time are already withheld from LLM providers. But exact planetary positions identify the birth moment: the set of planet longitudes pins down the date, the ascendant degree pins down the time to within seconds or minutes (it moves about 1° per 4 minutes), and date + time + ascendant/cusps can narrow down the location.
- **Decision (ACCEPTED):** every payload sent to an AI provider is treated as **potentially identifying personal data**, and is minimised.
- **Minimisation measures (precision values PROPOSED, Q-011):**
  - Send computed **categorical facts** by `fact_id` (sign, house, nakshatra, pada, lords, sub-lords, karakas, yogas, dasha lords) rather than raw longitudes.
  - Where a degree is needed for interpretation, send it rounded (PROPOSED: whole degree). Never send full-precision longitudes, cusp degrees, or ayanamsha values.
  - Boundary proximity is sent as a flag (`near_boundary: true`), not as a distance.
  - Dasha periods: only those overlapping the question's time window, with dates at month precision (PROPOSED). Never send the birth date or dasha balance at birth.
  - No database IDs, chart IDs, or record labels; per-request random correlation ID only.
  - The UI warns that the free-text question is sent to the provider.
  - Provider retention/training settings recorded before activation (D-012, [security.md](security.md) §4).
- **Residual risk (documented):** rounding reduces precision but does **not** anonymise. A set of categorical facts can still narrow down the birth date. The owner accepts this residual risk for their personal use under D-001. Re-assess before any multi-user use.
- **Verification required:** payload snapshot tests assert no field exceeds the configured precision and no forbidden fields appear; the evaluation compares reading quality with minimised vs full payload once to confirm minimisation does not degrade results (results recorded here).
- **Open questions:** Q-011.
- **History:** 2026-11-18 (the decision above is unchanged). Groq Zero Data Retention is **UNCONFIRMED** on the owner's account (D-012). Until confirmed, provider traffic is handled as if Groq may keep it for up to 30 days in the United States, under the precautions in [security.md](security.md) §4. This makes the minimisation rules and the "synthetic charts only" rule for evaluation runs the operative protection.

## D-028 Progressive evaluation framework — ACCEPTED (2026-11-17)

- **Decision:** the evaluation framework is built **incrementally from the research milestone onward**, not as one late phase. Each milestone delivers its evaluation increment, and a feature is not done until its golden cases and suite exist:

| Milestone | Evaluation increment |
|---|---|
| M2 Library & research | Golden-case and rule schemas; source-fidelity checks (citation exists, passage review status, rule ↔ citation support); first PROVISIONAL cases drafted alongside rules |
| M3 Evaluation core | Runner, comparators, reports, versioning, freeze mechanism |
| M4 Astronomy | Astronomy + shared-chart suites (Track D) |
| M5 Engines | Parashari, KP, Jaimini suites (Track D), grown with each feature |
| M6 Readings | Reading, comparison, adversarial suites (Track I) in en + hi; automatic checks; judge harness |
| M7 Opus evaluation | Full run, dataset freeze v1.0.0, baselines |

- **Consequences:** implementation plan tasks carry an "evaluation increment" line; CI runs Track D suites from M4 onward.
- **History:** 2026-11-17 clarification (owner-approved documentation correction; the decision is unchanged): "Track D suites from M4 onward" means the **calculation-engine** suites (`astronomy`, `chart`, `parashari`, `kp`, `jaimini`). Source-fidelity and citation checks from the M2 row run in CI as soon as they exist, before M4. During M3, rule-record and source-attribution checks expand as the knowledge base grows.

## D-029 Hindi evaluation suites — ACCEPTED (2026-11-17)

- **Decision:** Hindi versions of the **reading**, **comparison**, and **adversarial** suites: `reading-hi`, `comparison-hi`, `adversarial-hi`, mirroring `reading-en`, `comparison-en`, `adversarial-en`.
- Hindi cases share the language-neutral expectations of their English twin (fact IDs, rule IDs, citations, attribution, prohibited claims) and add language checks (Hindi output in Devanagari, glossary terms used correctly, Sanskrit terms consistent).
- Thresholds apply **per language** and are reported separately. A Hindi failure blocks approval just like an English one.
- **Verification required:** before Opus judge verdicts on Hindi are trusted, calibrate the judge against owner ratings on a Hindi sample (Q-013).
- **Open questions:** Q-013.
- **History:** 2026-11-18 owner direction (the decision above is unchanged): Hindi judge calibration must be **completed before any result is described as a calibrated Hindi evaluation**. It does **not** block building Hindi UI, prompts, or `*-hi` test cases. Until calibration is done, Hindi tier 2 verdicts are labelled "uncalibrated / advisory" in every report. "Opus judge" in the text above now reads "the evaluation judge model" (D-030, Q-018).

## D-030 No Anthropic model in the product; Groq Qwen is the only runtime provider — ACCEPTED (owner, 2026-11-18)

- **Context:** The owner stated: "we are not going to use any anthropic model. i am using claude code to write code. for groq model, model id is `qwen/qwen3.8-27b`." Earlier decisions (D-022, D-023, the plan's Stage A/B split, `ANTHROPIC_API_KEY`, Q-016) assumed a configured Anthropic Opus model as Stage A runtime and as evaluation judge.
- **Decision:**
  1. The application makes **no call to any Anthropic model**: no runtime, no judge. No `ANTHROPIC_API_KEY` is needed. Anthropic adapter work (T6.1) is dropped.
  2. The only runtime provider is **Groq**, with the model recorded in the D-012 register (`qwen/qwen3.8-27b`, owner-provided, catalogue-checked 2026-11-18). Model ID stays configuration only.
  3. **Claude Code** is the coding and research tool the owner uses to write the project. It is not an app setting and not an API integration. Records it drafts carry `{actor: CLAUDE_CODE}`. The "research/review model" role is therefore Claude Code, and the rule "no model is the sole authority for its own drafts" (D-022) applies to it.
  4. The **evaluation judge** model is **undecided** (Q-018). Anthropic is excluded. Until Q-018 is answered, Track I tier 2 has no judge: Track D, Track I tier 1 (automatic checks) and the harness work continue, and no tier 2 result is claimed.
  5. The two-stage plan collapses: there is no separate Anthropic "Stage A" baseline. The first full evaluation (M7) uses the Qwen runtime. If Qwen is also the judge, the run is **self-judged** (D-022) and the higher spot-check rate applies (Q-012).
- **Supersedes (in part):** D-022 (Opus as judge), D-023 (wording "initial Opus evaluation"), implementation-plan T6.0/T6.1/T7.1/T7.6/M8 wording, and the Anthropic items in deployment/architecture/security/testing docs. Those docs are updated in the same change; no earlier History line is edited.
- **Alternatives:** keep Anthropic for judging only (rejected by the owner); use another Groq-hosted model as judge (candidate for Q-018).
- **Consequences:**
  - Provider-payload minimisation (D-027) and privacy documentation now concern **Groq only**. Groq's retention facts are recorded in D-012.
  - The **runtime model is a Preview model** (D-012). Groq says Preview models "may be discontinued at short notice" and has already retired two Qwen models in 2026. Every reading, evaluation run, and baseline stores the exact model ID returned (CLAUDE.md rule 7), so a retirement is detectable. Q-019 asks the owner how to handle it.
  - `.env.example` and compose files carry no Anthropic variable. `EVAL_JUDGE_PROVIDER` / `EVAL_JUDGE_MODEL_ID` stay, with no value, until Q-018.
- **Open questions:** Q-018, Q-019. Q-016 is withdrawn.
- **History:** 2026-11-18 (second owner message; the decision text above is unchanged). (1) Owner **confirmed** no Anthropic model is selected; Q-016 stays withdrawn and the historical entries are preserved. (2) **Q-018 answered by owner proposal:** the evaluation judge is the same Groq model as the runtime (`qwen/qwen3.8-27b`). Point 4 above ("judge undecided") is therefore superseded by this line. Consequences: every Track I run is **self-judged** (weakest judge independence, D-022); the 25% spot-check rate applies (Q-012, itself still PROPOSED); Hindi tier 2 stays "uncalibrated" until Q-013; judge and runtime configuration are still stored separately so a different judge can be chosen later by a new History line; tier 2 verdicts remain advisory evidence and never the sole basis for VERIFIED. (3) **Q-019 partly answered:** Preview accepted for the initial experimental runtime; fallback policy, thinking vs instruct mode, and ZDR remain open. (4) **ZDR UNCONFIRMED**, not assumed (D-012). (5) **Gate:** no real model call until the provider configuration and data-handling requirements are approved by the owner. Fake-provider work continues.
- **History:** 2026-11-18 (third owner message; the decision text and earlier History lines are unchanged). **Q-018 is provisionally accepted** as a **self-judged Qwen evaluation configuration**. Every such evaluation run is labelled **SELF_JUDGED**. The Q-012 spot-check rule applies with the self-judged rate: review **every failure** and sample **25%** of passing cases (minimum 5 only when at least 5 eligible passes exist; never more than exist). **Self-judged results are advisory and cannot independently establish VERIFIED status.** Implemented as pure policy code and tests in `evaluation/policy.py` (no model is called). "Provisionally" means the owner may still choose a different judge later by a new History line.

## D-031 Rule knowledge base schema, lifecycle, approval audit and retrieval gate — PROPOSED

- **Context:** Milestone M2 needs a rule record format and validator before any rule is written (T2.6). The owner directed these **requirements** on 2026-11-18: separate Parashari, KP, Jaimini and shared namespaces; validated unique IDs, metadata, source references, types, statuses and versions; calculation rules, calculation conventions and interpretive rules kept apart; conflicting traditions and interpretations preserved as separate records; a rule lifecycle with explicit owner approval; unapproved research drafts never reaching runtime retrieval; version history and approval audit records preserved; the validator in CI; no complete book ingestion or purchase needed; no AI provider calls.
- **Proposal (design, built in M2; full reference [rule-schema.md](rule-schema.md)):**
  - One YAML file per rule, `knowledge/rules/<namespace>/<RULE_ID>.yaml`, namespaces `parashari` (`PAR`), `kp` (`KP`), `jaimini` (`JAI`) and a new `shared` (`SHR`). Topic codes come from a controlled vocabulary file. This adds the `SHR` prefix and `shared` directory to the ID pattern in data-model.md §4.4.
  - Three rule types: `CALCULATION_RULE`, `CALCULATION_CONVENTION` (tied to a `D-NNN` decision; cannot be VERIFIED while that decision is not ACCEPTED), `INTERPRETIVE_RULE`. Content models forbid fields of another type.
  - Statuses `DRAFT` (new, for incomplete working notes), `PROVISIONAL`, `VERIFIED`, `CONFLICTING_SOURCES`, `REJECTED`, kept **per version**. Content of a recorded version is immutable (hash-checked); status changes are append-only lifecycle events; reviews are append-only audit records bound to a version and its content hash.
  - **Only the owner** can record VERIFIED or REJECTED, through `jyotish rules approve` (interactive terminal only, exact rule ID typed, result re-validated and rolled back if invalid). Approval resets with every new version.
  - Append-only history is checked against git (`jyotish rules validate --against REF`).
  - Runtime retrieval refuses to run on an invalid rulebase, serves only the highest VERIFIED version after an independent approval re-check, serves conflicting records separately with links, and filters by tradition (+ shared).
  - A source catalogue schema (T2.1a) with `ownership: UNCONFIRMED` by default, so nothing is ingested for an unconfirmed book (Q-014).
- **Alternatives:** one file per version (simpler diffs, but approval and lifecycle spread over many files); relations outside version content (less re-approval churn, but a conflict could change after approval without a new version); a database as source of truth (rejected earlier, D-018); cryptographic signing of owner approvals (Q-020).
- **Verification required:** the validator has a negative test for every code and positive tests for every type, status and namespace; mutation checks showed the tests fail when the hash, owner-only, decision-acceptance or retrieval checks are disabled; the real repository validates with zero errors in the Track D CI stage.
- **Consequences:** adding a `DRAFT` status and the `SHR` namespace extends data-model.md §4.4 (updated in the same change, no ACCEPTED decision altered). Conventions D-003 to D-010 and D-025 stay PROPOSED, so no convention built on them can be VERIFIED.
- **Limits stated plainly:** the validator proves internal consistency, not Jyotish correctness, and cannot prove who typed an approval (Q-020).
- **Open questions:** Q-020, Q-021.

---

## Open questions

Unresolved. Do not invent answers. Each must be answered by the owner or by a cited source, and the answer recorded in the linked decision.

### Current status of every question (updated 2026-11-18)

The original question rows below are kept unchanged. This table is the current state; the dated record of what the owner said is in "Owner decision log (T1.9)" at the end of this file.

| ID | Status | Note |
|---|---|---|
| Q-001 | OPEN | Lahiri variant. Blocks finalising Parashari/Jaimini ayanamsha results (M4) |
| Q-002 | OPEN | KP ayanamsha variant (M4/M5b) |
| Q-003 | OPEN | Node convention per tradition (M4+) |
| Q-004 | OPEN | Placidus undefined at high latitude (M5b) |
| Q-005 | OPEN | KP sub-boundary inclusivity vs reference tables (M5b) |
| Q-006 | **ANSWERED 2026-11-18** | No default Jaimini karaka profile; user must explicitly choose 7k or 8k (D-007 History) |
| Q-007 | OPEN | Karaka scheme in K.N. Rao's book; whether karakas enter the dasha calculation |
| Q-008 | OPEN | Exact edition of the K.N. Rao book (needs the owner's copy) |
| Q-009 | OPEN | The eight Chara Dasha steps; no code until VERIFIED |
| Q-010 | OPEN | Vimshottari year length (D-025 stays PROPOSED) |
| Q-011 | OPEN | Payload precision values (D-027 values stay PROPOSED) |
| Q-012 | **PROPOSED, provisionally accepted by owner 2026-11-18** | Rule usable meanwhile; final status is not approved and stays PROPOSED until the owner explicitly approves it |
| Q-013 | OPEN | Hindi judge calibration must finish before any "calibrated Hindi results" claim; does not block Hindi development |
| Q-014 | OPEN | Owner has **not** confirmed owning any recommended book. Inventory is UNCONFIRMED |
| Q-015 | OPEN | Per-source copyright status |
| Q-016 | **WITHDRAWN 2026-11-18** (owner confirmed the same day) | No Anthropic model in the product (D-030). Not answered; no longer applicable. Historical entries preserved |
| Q-017 | **ANSWERED 2026-11-18** | Chara Dasha needs both a source-approved specification and an independent calculation check; otherwise unavailable in the initial release (D-008 History) |
| Q-018 | **PROVISIONALLY ACCEPTED 2026-11-18 (owner)** | Self-judged Qwen configuration: judge = the same Groq model as the runtime. Every run is labelled **SELF_JUDGED**; review all failures and 25% of passes; results are advisory and cannot independently establish VERIFIED (D-030 History). A different judge can be chosen later by a new History line |
| Q-019 | **PARTLY ANSWERED 2026-11-18** | Preview model accepted as the initial experimental runtime. **Still open:** fallback if Groq retires it; thinking vs instruct mode; Zero Data Retention (**UNCONFIRMED**, not assumed) |
| Q-020 | OPEN (new) | How strongly must owner approvals of rules be authenticated (e.g. signing with an owner-held key)? Until answered, D-031's controls apply (interactive-only command, version-bound hash, append-only history check, owner reviews diffs) |
| Q-021 | OPEN (new) | Should runtime retrieval keep serving the last VERIFIED version while a newer version is drafted (current behaviour), or take the rule offline until the new version is approved? |

| ID | Question | Linked | How to resolve |
|---|---|---|---|
| Q-001 | Which Lahiri variant (`SE_SIDM_LAHIRI` vs 1940 / VP285 / ICRC) matches the owner's Parashari/Jaimini references? | D-003 | Compare values with Indian Astronomical Ephemeris and owner's reference software |
| Q-002 | KP ayanamsha: original Krishnamurti or KP "New"/VP291? | D-003 | KP Reader I / KP ephemeris worked examples |
| Q-003 | Do the owner's KP and Jaimini sources use mean or true node? Should any profile default to true? | D-004 | Source passages; owner preference |
| Q-004 | KP charts at latitudes where Placidus is undefined: refuse, or allow a documented alternative? | D-005 | KP sources; owner decision |
| Q-005 | Does the start-inclusive sub boundary match the KP reference tables? | D-006 | Entry-by-entry table comparison |
| Q-006 | Which Jaimini karaka profile (7k or 8k) should the UI preselect, if any? | D-007 | Owner decision |
| Q-007 | Which karaka scheme does K.N. Rao's book use, and do karakas affect the Chara Dasha **calculation** or only interpretation? | D-007, D-008 | Cited passages from the exact edition |
| Q-008 | Exact edition, publisher, year (and ISBN) of the owner's copy of *Predicting Through Jaimini's Chara Dasha* | D-008, D-011 | Owner's copy |
| Q-009 | The eight Chara Dasha calculation steps listed in D-008 | D-008 | Claude Code drafts rule records citing the exact edition; owner approves source and evidence; independent check recorded where one exists (D-008 rev. 3) |
| Q-010 | Which Vimshottari year length do the owner's sources and reference software use? | D-025 | Worked examples; software settings |
| Q-011 | Payload precision levels (degree rounding, dasha date precision); does minimisation reduce reading quality? | D-027 | One comparison evaluation run |
| Q-012 | Owner spot-check sampling rule. PROPOSED, per suite and language: review **all failed cases**; sample **10%** of eligible passing cases (**25%** when the run is self-judged), rounded up; apply a minimum of **5** passing cases only when at least 5 eligible passing cases exist; if fewer than 5 exist, review all of them; never select more cases than exist. Selection method (PROPOSED: random with recorded seed), eligible count, selected case IDs, and sample size are recorded in the evaluation report. | D-022 | Owner decision |
| Q-013 | Is Opus judge agreement with owner ratings adequate in Hindi (PROPOSED threshold ≥ 90% agreement on a calibration set)? | D-029 | Calibration run |
| Q-014 | Which recommended books does the owner already have, and in which editions/formats? | D-011 | Owner inventory |
| Q-015 | Translator/commentator death years and resulting copyright status for each source | D-011 | Per-source check |
| Q-016 | Exact API model ID of the configured Anthropic Opus model (runtime Stage A and evaluation judge). Unverified; no ID is assumed. | D-022, D-026; register above | Check Anthropic's official model catalogue / API documentation before T6.0; record ID, date, and source in the register. Does not block M1. |
| Q-017 | For D-008: if no independent implementation or qualified reviewer can be found for K.N. Rao Chara Dasha, what evidence is enough to make it available? Until answered, the availability gate stays closed. | D-008 | Owner decision |
| Q-018 | Added 2026-11-18. With no Anthropic model (D-030), **which model acts as the Track I tier 2 evaluation judge**? Options: (a) the Groq Qwen runtime model itself (always self-judged, 25% spot-check rate, weakest independence); (b) a different Groq-hosted model (needs its own catalogue check and register entry; independent of the runtime but still a model); (c) no tier 2 judge: tier 1 automatic checks plus owner spot-checks only (cheapest, but more owner review work, which the owner should not be asked to do as specialist validation). Claude Code makes no recommendation until the owner has chosen how much judge independence they want. | D-022, D-030 | Owner decision. Blocks only deliberate Track I tier 2 runs (M7). Does not block M1–M6 |
| Q-019 | Added 2026-11-18. Groq lists `qwen/qwen3.8-27b` as **Preview** ("evaluation purposes only ... may be discontinued at short notice"). Does the owner accept it as the only runtime model for release 1? If Groq retires it, what is the fallback: a named successor, another Groq model, or pause AI features? Also: which Qwen mode is used (thinking vs instruct) and is Groq Zero Data Retention enabled on the owner's account? | D-012, D-030, D-027 | Owner decision. Blocks only M6+ model-dependent work; the provider adapter and fake provider proceed meanwhile |
| Q-020 | Added 2026-11-18. The validator proves rule records are consistent but cannot prove **who** typed an owner approval (anyone with write access could type a `CLI_INTERACTIVE` entry). How strongly must owner approvals be authenticated? Options: keep the current controls (interactive-only command, content-hash binding, git append-only check, owner reviews diffs); require signed commits for changes touching `reviews`/`lifecycle`; sign approvals with a key held by the owner. | D-031 | Owner decision. Does not block M2 work; becomes important before real rules are approved |
| Q-021 | Added 2026-11-18. While a rule's newer version is only DRAFT/PROVISIONAL, retrieval currently keeps serving the last VERIFIED version (and a REJECTED newer version leaves it in place). Is that right, or should a rule go offline until its new version is approved? | D-031 | Owner decision. Does not block M2 work |

---

## Changelog

| Date | Change |
|---|---|
| 2026-11-17 | Initial docs set created from `integrated_jyotish_project_plan.md`. D-001, D-002 accepted by owner; D-003–D-025 proposed. |
| 2026-11-17 | Post-review documentation correction (owner-approved). **D-008** rev. 3 (responsibilities and gates; History added; still PROPOSED; implementation block unchanged). **D-028** clarification added as a History line; ACCEPTED text and meaning unchanged. **Q-009** resolution path and **Q-012** sampling rule updated (both still open/PROPOSED). **Q-016** (Anthropic model ID) and **Q-017** (Chara Dasha availability without independent check) added. Terminology note, verification-roles note, and Model ID verification register added. Consistency fixes elsewhere: model naming, explicit Jaimini profile selection, R1 varga list, Chara Dasha shown as unavailable, provenance fields, `dasha_year_days` scope, progressive-testing timing. No OPEN question was resolved and no status changed. |
| 2026-11-17 | Architecture review (owner-directed): D-022 and D-023 revised and ACCEPTED; D-003, D-004, D-005, D-007, D-008, D-011, D-025 revised (rev. 2, still PROPOSED/OPEN, with history lines); D-027, D-028, D-029 added; standard PROPOSED entry structure and Open questions Q-001–Q-015 added. Profile keys renamed: `parashari-default` → `parashari-lahiri`, `kp-default` → `kp-krishnamurti`, `jaimini-default` → `jaimini-lahiri-7k` / `jaimini-lahiri-8k`. |
| 2026-11-18 | **Owner decisions at the start of M1 (T1.9).** **D-030** added (ACCEPTED): no Anthropic model in the product; Groq Qwen only; D-022/D-023 partly superseded via History lines. **D-012**: ID `qwen/qwen3.8-27b` recorded after Claude Code checked Groq's official catalogue (status Preview; retention facts recorded). **Q-006** answered (no default Jaimini profile). **Q-017** answered (Chara Dasha needs source-approved specification + independent calculation check). **Q-012** provisionally accepted, status kept PROPOSED. **Q-014** stays open (inventory unconfirmed). **Q-016** withdrawn. **Q-018**, **Q-019** added. D-003–D-010 and D-025 confirmed as staying PROPOSED. History lines appended to D-007, D-008, D-014, D-022, D-023, D-029 (T1.1 observations in D-014); no earlier History line was edited or removed. |
| 2026-11-18 | **Second owner message.** Q-016 withdrawal confirmed. **Q-018** answered by owner proposal (judge = the runtime Groq model, so all runs are self-judged; register row added). **Q-019** partly answered (Preview accepted as initial experimental runtime; fallback, mode and ZDR still open). **Groq ZDR recorded as UNCONFIRMED** (D-012, D-027 History lines). Gate added: no real model call before the owner approves provider configuration and data-handling requirements. Git remote creation blocked: GitHub CLI is not authenticated. History lines appended to D-012, D-027, D-030; no earlier line edited. |
| 2026-11-18 | **Third owner message: M2 start.** **D-031** added (PROPOSED): rule knowledge base schema, lifecycle, approval audit and retrieval gate; **Q-020** (authentication of owner approvals) and **Q-021** (retrieval while a newer version is drafted) opened. **Q-018** recorded as provisionally accepted (self-judged Qwen configuration: every run labelled SELF_JUDGED, 25% pass-case sampling, every failure reviewed, results advisory and unable to establish VERIFIED); History line appended to D-030. Q-012 stays PROPOSED. No question was resolved by assumption; Q-006, Q-014, Q-016, Q-017, Q-019 and ZDR status are unchanged. |

## Owner decision log (T1.9)

Dated record of what the owner said at the start of M1, 2026-11-18, and what Claude Code did with it. Verbatim intent is kept; nothing here changes an earlier History entry. Verification roles follow [testing.md](testing.md) §7: source approval, automated tests, independent calculation checks, and owner approval are four different things, and the owner is **not** represented as a Jyotish expert or asked to validate calculations personally.

| # | Owner instruction | Recorded as | Effect on work |
|---|---|---|---|
| 1 | Q-006: no default Jaimini karaka profile; the user must explicitly choose 7-karaka or 8-karaka. | Q-006 ANSWERED; D-007 History | Docs that said "while Q-006 is open" now say "no default (owner decision)". Nothing may preselect a Jaimini profile. |
| 2 | Q-012: accept the proposed spot-check sampling rule **provisionally**: review all failures; 10% of passes (25% if self-judged); minimum 5 only when ≥ 5 eligible cases exist; never more than exist. Keep PROPOSED until the owner explicitly approves its final status. | Q-012 "PROPOSED, provisionally accepted" | Rule stays as written in testing.md §6.4; status stays PROPOSED. |
| 3 | Q-014: do not assume the owner owns any recommended book. Inventory stays unconfirmed. M2 infrastructure may proceed; book-specific ingestion waits. | Q-014 OPEN | T2.1 is split in implementation-plan.md: infrastructure tasks proceed, ingestion of any named book is blocked until the owner supplies the inventory. D-011 stays OPEN. |
| 4 | D-003–D-010 and D-025 stay PROPOSED. Do not turn them into accepted defaults or finalise dependent calculation results without the required research and approval. | Unchanged (still PROPOSED) | Calculation work may use them only as labelled, test-covered PROPOSED values in versioned profiles. Results are labelled provisional. |
| 5 | No Anthropic model; Groq model ID `qwen/qwen3.8-27b`. Claude Code is used to write code. | D-030; D-012 register; Q-016 withdrawn; Q-018, Q-019 added | See D-030 and D-012. |
| 6 | Chara Dasha / Q-017: unavailable in the initial release unless its method has a source-approved specification **and** an independent calculation check. Other Jaimini work continues under its own gates. | Q-017 ANSWERED; D-008 History | Availability gate unchanged in effect; wording tightened. |
| 7 | Q-013: Hindi judge calibration must be completed before claiming calibrated Hindi results; it must not block Hindi functionality and test cases. | D-029 History; Q-013 OPEN | Hindi development and `*-hi` cases proceed. Reports label Hindi tier 2 "uncalibrated" until calibration. |
| 8 | Keep building automated source checks, calculation tests, evaluation infrastructure and the golden dataset progressively; not postponed to M8. | Already D-028; reinforced | M1 ships the Track D CI slot and the `evaluation/` layout; each later milestone ships its increment. |
| 9 | Keep source approval, automated tests, independent calculation checks, and owner approval distinct. Do not present the owner as a Jyotish expert. | Already testing.md §7; reinforced | No change to wording; checked in new docs. |
| 10 | Keep all unresolved questions visible; do not resolve to make implementation easier. | "Current status of every question" table | All other questions remain OPEN. |

### Second owner message, 2026-11-18

| # | Owner instruction | Recorded as | Effect on work |
|---|---|---|---|
| 11 | Q-016: confirm no Anthropic model is selected; keep Q-016 withdrawn and preserve historical entries. | Q-016 WITHDRAWN (confirmed); D-030 History | No change to history; nothing deleted. |
| 12 | Q-018: owner proposes the judge model `qwen/qwen3.8-27b`. | Q-018 ANSWERED (owner proposal); register row; D-030 History | Judge = runtime model, so all runs are self-judged; 25% spot-check rate. |
| 13 | Q-019: accept `qwen/qwen3.8-27b` as the initial experimental runtime, subject to Preview status and limitations. | Q-019 PARTLY ANSWERED | Fallback policy, thinking/instruct mode and ZDR remain open. |
| 14 | Groq ZDR cannot be confirmed; keep UNCONFIRMED; do not assume enabled; document precautions until confirmed. | D-012, D-027 History; security.md §4 | Precautions and a first-real-call gate are documented. |
| 15 | No real model calls until provider configuration and data-handling requirements are approved. | security.md §4 gate; CLAUDE.md prohibited actions | Only the fake provider is used. Local `.env` model settings stay empty. |
| 16 | Prepare a private GitHub remote (create it only if GitHub CLI authentication exists, otherwise give exact steps); pre-commit checks; initial commit and push; run CI and report. | implementation-plan T1.2 | GitHub CLI is **not** authenticated on this machine, so the remote, push and GitHub CI run are blocked on the owner (exact steps given). Pre-commit checks and the local commit are done. |
| 17 | M2 infrastructure may proceed independently. | implementation-plan | Allowed; see the task list. |

### Third owner message, 2026-11-18 (M2 start)

| # | Owner instruction | Recorded as | Effect on work |
|---|---|---|---|
| 18 | Proceed with M2 infrastructure; do not wait for the GitHub remote. Start with the rule YAML schema and `jyotish rules validate`. | implementation-plan M2 status | Built: T2.6, T2.9 approval records, T2.1a source-catalogue schema, first T2.8 Track D checks. |
| 19 | Rule requirements: namespaces, validated metadata, three rule kinds, preserved conflicts, owner-approval lifecycle, no unapproved drafts in retrieval, preserved version history and audit, comprehensive tests, validator in CI, no book ingestion, no provider calls, preserve decision history and open questions. | D-031 (PROPOSED), docs/rule-schema.md | All implemented; see rule-schema.md. No book was ingested and no provider was called. |
| 20 | Q-018 provisionally accepted as a self-judged Qwen configuration; mark every such run SELF_JUDGED; 25% pass-case rule; review every failure; self-judged results are advisory and cannot independently establish VERIFIED. | D-030 History; Q-018 row; `evaluation/policy.py` | Policy encoded and tested; the runner (M3) must use it. |
| 21 | Keep the first-real-call gate closed; ZDR UNCONFIRMED; no real personal birth data to AI providers. | unchanged (security.md §4) | No provider call; `RUNTIME_*` stay empty. |
| 22 | Report files, schema examples, validator commands, tests and blockers; do not claim M2 complete until exit checks pass. | implementation-plan M2 status | M2 is **not** complete; remaining tasks listed there. |
