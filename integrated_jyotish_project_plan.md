# Integrated Jyotish Research & Software Development Plan

## Parashari + KP + Jaimini

**Project objective:** Build a professional, research-grade Jyotish
platform that combines Parashari, Krishnamurti Paddhati (KP), and
Jaimini astrology while preserving the distinct rules and calculation
conventions of each tradition.

The system will use a shared astronomical foundation, separate
tradition-specific engines, a source-grounded knowledge library, an
integrated interpretation layer, and an automated evaluation framework.

------------------------------------------------------------------------

## 1. Project goals and operating principles

### Goals

1.  Build reliable astronomical and chart-calculation foundations.
2.  Implement Parashari, KP, and Jaimini as distinct systems.
3.  Create a searchable library of classical texts, translations,
    commentaries, and research material.
4.  Use AI to assist with research, rule extraction, software
    development, and interpretation.
5.  Establish a versioned golden dataset and repeatable evaluation
    framework.
6.  Use evaluation results to validate the initial system and assess
    future AI-model migrations.
7.  Make the development process manageable for a project owner who does
    not intend to become a Jyotish specialist or programmer.

### Core principles

-   **Source before rule:** Classical claims must be traceable to an
    identified source, edition, chapter, page, or verse wherever
    possible.
-   **Keep traditions distinct:** Parashari, KP, and Jaimini rules must
    not be silently mixed or treated as interchangeable.
-   **Separate calculation from interpretation:** Deterministic
    calculations should be performed by tested software, not improvised
    by an LLM.
-   **Preserve conventions:** Where traditions use different calculation
    conventions, record and implement them explicitly.
-   **Record uncertainty:** Conflicting sources, uncertain translations,
    and unresolved interpretations must remain visible.
-   **Reproducibility:** Record software, model, prompt, configuration,
    and dataset versions for test runs.
-   **No unsupported claims:** AI-generated interpretations must
    distinguish source-backed rules, calculated facts, inference, and
    uncertainty.
-   **Evaluation is deliberate, not continuous:** Opus is used for
    initial development validation and future model migrations, not for
    every ordinary user request.

------------------------------------------------------------------------

## 2. Overall system architecture

``` text
                         JYOTISH RESEARCH PLATFORM
                                    |
                  +-----------------+-----------------+
                  |                                   |
       SOURCE & KNOWLEDGE LIBRARY             DEVELOPMENT WORKFLOW
       Books, Sanskrit, translations,          Claude Code
       commentaries, rule records              Opus 5.5 initially
                  |                                   |
                  +-----------------+-----------------+
                                    |
                      SHARED ASTRONOMICAL FOUNDATION
             Birth data | Time zones | Ephemeris | Ayanamsha
                 Planetary positions | Common chart data
                                    |
             +----------------------+----------------------+
             |                      |                      |
       PARASHARI ENGINE          KP ENGINE            JAIMINI ENGINE
       Graha aspects             Nakshatra lords       Chara Karakas
       Yogas                     Sub-lords             Rashi Drishti
       Shadbala                  Cuspal analysis       Argala
       Divisional charts         Significators         Jaimini Dashas
       Vimshottari Dasha         Ruling planets        Other defined rules
             |                      |                      |
             +----------------------+----------------------+
                                    |
                       INTEGRATED INTERPRETATION LAYER
             Individual readings | Comparison | Combined reading
                                    |
                      AI INTERPRETATION: GROQ QWEN 3.8
                                    |
                         APPLICATION / USER INTERFACE

       CROSS-CUTTING QUALITY SYSTEM:
       Golden dataset | Automated tests | Regression tests
       Model migration evaluation | Reports and version history
```

The diagram is conceptual. The implementation should keep shared
services reusable while preserving system-specific calculation and
interpretation logic.

------------------------------------------------------------------------

## 3. Shared astronomical foundation

This layer supplies the astronomical and birth-chart data required by
the three systems.

### Scope

-   Birth date and local birth time.
-   Birthplace and geographic coordinates.
-   Historical time-zone and daylight-saving handling where applicable.
-   Conversion to UTC and Julian Day.
-   Ephemeris calculations.
-   Planetary longitudes, latitudes, speeds, and retrograde status as
    required.
-   Ayanamsha configuration and explicit recording of the selected
    method.
-   Ascendant and relevant chart reference points.
-   Sign, degree, nakshatra, pada, and other common derived positions.
-   House and cusp data where required by the selected tradition.
-   Precision, rounding, and boundary-handling policies.

### Important design requirements

1.  Store original birth inputs separately from normalized calculation
    inputs.
2.  Preserve the selected ayanamsha and calculation settings with every
    chart.
3.  Do not assume all three traditions use identical house, cusp, or
    ayanamsha conventions.
4.  Provide an explicit configuration profile for each tradition.
5.  Make calculations deterministic and independently testable.
6.  Record ephemeris library and version.
7.  Investigate Swiss Ephemeris licensing before deciding how the
    software will be distributed.

### Initial decisions to document

-   Ayanamsha options and defaults.
-   KP ayanamsha convention and any required variants.
-   Node calculation convention.
-   House and cusp calculation methods.
-   Treatment of birth-time uncertainty.
-   Historical time-zone data source.
-   Ephemeris and licensing choice.

These choices should be researched and documented before implementation
is treated as final.

------------------------------------------------------------------------

## 4. Parashari system

Implement Parashari as an independent rule and interpretation engine.

### Initial scope

-   Graha aspects.
-   Sign and house lordships.
-   Planetary dignity and condition.
-   Yogas and their conditions, exceptions, and cancellation rules where
    supported.
-   Shadbala and its components.
-   Divisional charts (vargas), with an explicitly defined initial
    scope.
-   Vimshottari Dasha and sub-periods.
-   Relevant transit rules, if included in the agreed product scope.
-   Parashari-specific interpretation and source citations.

### Requirements

-   Each implemented rule must have a unique identifier.
-   Store its source references, translation/commentary basis,
    conditions, exceptions, and formal specification.
-   Separate calculation logic from interpretive text.
-   Add unit tests and boundary tests for every implemented calculation
    or rule.
-   Where classical sources disagree, preserve competing interpretations
    rather than silently choosing one.

------------------------------------------------------------------------

## 5. KP system

Implement KP as a separate system with its own documented conventions.

### Initial scope

-   Nakshatra lord calculations.
-   Sub-lord and relevant sub-division calculations.
-   Cuspal positions and cuspal sub-lords.
-   Significators and their derivation.
-   Ruling planets.
-   KP-specific house and cusp analysis.
-   KP-specific interpretation workflows and source citations.

### Requirements

-   Document the exact KP calculation conventions and precision
    requirements.
-   Test cusp and sub-lord boundary cases carefully.
-   Keep KP significator logic separate from Parashari house-lord or
    aspect logic.
-   Record the source and version of each implemented rule.
-   Do not infer missing KP rules from general Parashari principles.

------------------------------------------------------------------------

## 6. Jaimini system

Implement Jaimini as a separate system with its own source catalogue and
rule specifications.

### Initial scope

-   Chara Karakas and the selected calculation convention.
-   Rashi Drishti.
-   Argala and relevant obstruction rules.
-   Jaimini Dashas, beginning with explicitly selected and documented
    methods.
-   Relevant sign-based and karaka-based interpretation rules.
-   Jaimini-specific interpretation and source citations.

### Requirements

-   Document the selected Chara Karaka convention, including treatment
    of Rahu if applicable.
-   Define the supported Jaimini Dasha methods rather than treating
    "Jaimini Dasha" as one unspecified calculation.
-   Keep Jaimini sign aspects and interpretive rules separate from
    Parashari graha aspects.
-   Preserve textual and commentary differences as separate rule
    records.
-   Create calculation and interpretation tests for each supported
    feature.

------------------------------------------------------------------------

## 7. Integrated interpretation layer

The integrated layer combines results from the three systems without
erasing their differences.

### User-facing modes

1.  **Parashari reading:** Uses Parashari calculations and rules only.
2.  **KP reading:** Uses KP calculations and rules only.
3.  **Jaimini reading:** Uses Jaimini calculations and rules only.
4.  **Comparative reading:** Presents the findings of each system side
    by side.
5.  **Optional combined interpretation:** Synthesizes findings while
    explicitly attributing each point to its originating tradition.

### Interpretation requirements

-   Show which system supports each conclusion.
-   Distinguish calculated chart facts from rules and interpretive
    inferences.
-   Include source references where the knowledge base supports them.
-   Identify agreement, disagreement, and silence between systems.
-   Do not manufacture consensus when systems disagree.
-   State uncertainty and missing evidence.
-   Keep the individual system readings available even when a combined
    reading is requested.

------------------------------------------------------------------------

## 8. AI architecture

### Development and research

**Claude Code** is the primary development environment and research
assistant. It will be used to:

-   Explore the supplied Jyotish books and source library.
-   Search for relevant passages and references.
-   Extract candidate rules and identify ambiguities.
-   Draft formal rule specifications.
-   Develop software modules and tests.
-   Maintain project documentation.
-   Help create the golden dataset and evaluation tooling.

Project instructions should be maintained in a `CLAUDE.md` file.
Specialist workflows may be organised as reusable skills or documented
procedures.

### Initial evaluator: Claude Opus 5.5

Opus 5.5 is used during initial development to:

-   Review the architecture and research methodology.
-   Challenge extracted rules and their source references.
-   Review golden dataset cases and expected results.
-   Identify missing conditions, exceptions, and ambiguous cases.
-   Review initial software and evaluation results.

Opus is not intended to evaluate every runtime answer or every routine
development action.

### Primary runtime model: Groq Qwen 3.8

After initial Opus testing and a controlled transition, Groq Qwen 3.8
becomes the primary AI model for application interpretation and other
agreed runtime AI tasks.

Before implementation, verify the exact model identifier and current
availability from Groq's official model catalogue. Do not hard-code an
assumed model ID.

### AI operating rules

-   LLMs must not be the source of truth for astronomical calculations.
-   LLMs should retrieve approved source material when making classical
    claims.
-   Runtime prompts should require clear attribution to Parashari, KP,
    or Jaimini.
-   Model output should be structured where practical, so tests can
    inspect it.
-   Preserve model and prompt versions for reproducibility.
-   Keep provider integration behind an adapter so models can be changed
    without rewriting the application.

------------------------------------------------------------------------

## 9. Book library and knowledge management

Create a searchable, versioned library for primary texts and supporting
research.

### Suggested structure

``` text
jyotish-library/
├── source-catalog/
├── parashari/
│   ├── primary-texts/
│   ├── translations/
│   └── commentaries/
├── kp/
│   ├── foundational-texts/
│   ├── reference-material/
│   └── commentaries/
├── jaimini/
│   ├── primary-texts/
│   ├── translations/
│   └── commentaries/
├── sanskrit/
├── research-notes/
└── extracted-text/
```

### Source metadata

For every source, record as available:

-   Title and author.
-   Edition, publisher, and publication year.
-   Language.
-   Translator and commentator.
-   File identifier and checksum.
-   Chapter, page, and verse mapping.
-   Copyright or usage restrictions.
-   OCR and transcription review status.

Keep original scans/PDFs unchanged. Store extracted text separately. OCR
output, especially Sanskrit and Devanagari, must be checked against page
images before it is treated as reliable evidence.

### Rule knowledge records

Each rule record should include:

-   Unique rule ID.
-   Tradition: Parashari, KP, or Jaimini.
-   Topic and Sanskrit/technical terminology.
-   Exact source and edition.
-   Chapter, page, verse, or passage.
-   Original text and translation where available.
-   Conditions and exceptions.
-   Formal, testable specification.
-   Interpretation notes.
-   Conflicting sources or alternative readings.
-   Verification status and revision history.

------------------------------------------------------------------------

## 10. Golden dataset and evaluation framework

The evaluation framework is a core project component. It is designed to
validate the initial system and to test future model migrations. It is
not intended to run Opus continuously during normal application use.

### 10.1 Golden dataset structure

Create separate, linked collections:

1.  **Astronomical reference cases:** Verified birth inputs and expected
    planetary/astronomical outputs.
2.  **Shared chart cases:** Expected common chart data and boundary
    cases.
3.  **Parashari cases:** Rule-specific inputs, expected outcomes,
    exceptions, and references.
4.  **KP cases:** Nakshatra, sub-lord, cusp, significator, and
    ruling-planet cases.
5.  **Jaimini cases:** Chara Karaka, Rashi Drishti, Argala, and Dasha
    cases.
6.  **Interpretation cases:** Questions, relevant chart facts, approved
    source evidence, expected content criteria, and prohibited
    unsupported claims.
7.  **Integration cases:** Tests that check correct comparison and
    attribution across the three systems.
8.  **Adversarial cases:** Ambiguous, incomplete, conflicting, or
    misleading inputs used to test whether the system acknowledges
    uncertainty.

### 10.2 Golden case format

A case should contain, as applicable:

-   Case ID and dataset version.
-   Tradition and topic.
-   Input chart or question.
-   Required calculation/configuration profile.
-   Expected deterministic outputs.
-   Expected rule IDs.
-   Source evidence and exact references.
-   Expected interpretation criteria.
-   Known ambiguities and acceptable alternatives.
-   Prohibited errors or claims.
-   Verification status and review history.

### 10.3 Verification workflow

1.  Claude Code researches source material and drafts cases.
2.  Claude Code proposes expected results and records evidence.
3.  Opus 5.5 independently reviews the cases and challenges weak
    reasoning.
4.  Deterministic calculations are checked against independent reference
    calculations or trusted implementations.
5.  The project owner cross-checks important and disputed textual claims
    using other models and independent sources.
6.  Cases that are adequately supported are approved; unresolved or
    conflicting cases remain separately labelled.
7.  The approved dataset is versioned and frozen as a benchmark.

AI agreement is supporting evidence, not proof. Opus must not be the
sole authority for approving cases it helped create.

### 10.4 Case status

Use explicit statuses such as:

-   `VERIFIED`
-   `PROVISIONAL`
-   `CONFLICTING_SOURCES`
-   `REJECTED`

Only approved, verified cases should enter the primary benchmark. Keep
provisional and conflicting cases in separate suites to test uncertainty
handling.

### 10.5 Automated evaluation suites

  -----------------------------------------------------------------------
  Suite                               What it tests
  ----------------------------------- -----------------------------------
  Astronomy                           Position accuracy, time conversion,
                                      ayanamsha, nodes, boundaries

  Chart construction                  Signs, houses, cusps, nakshatras,
                                      padas, vargas

  Parashari                           Aspects, lordships, yogas,
                                      Shadbala, Dashas

  KP                                  Nakshatra/sub-lords, cusps,
                                      significators, ruling planets

  Jaimini                             Karakas, Rashi Drishti, Argala,
                                      Dashas

  Source fidelity                     Whether citations exist and support
                                      the stated rule

  Sanskrit                            Terminology, transliteration,
                                      translation consistency

  Interpretation                      Required points, unsupported
                                      claims, attribution, uncertainty

  Integration                         Correct comparison without mixing
                                      traditions

  Regression                          Whether code, prompt, or model
                                      changes break previous results
  -----------------------------------------------------------------------

### 10.6 Evaluation methods

Use the right test method for each output:

-   Exact numerical comparison with tolerances for deterministic
    calculations.
-   Exact or structured comparison for categorical outputs such as sign,
    nakshatra, lord, or sub-lord.
-   Rule-based assertions for conditions and exceptions.
-   Source-reference checks against the source catalogue.
-   Human-reviewed criteria and structured rubrics for open-ended
    interpretation.
-   Repeated runs where model outputs may vary.
-   Regression comparisons against stored baseline results.

Do not use a single vague AI-generated "accuracy score" as the sole
quality measure. Report results by category and show individual
failures.

------------------------------------------------------------------------

## 11. Initial validation and model transition

The agreed sequence is:

### Stage A --- Build and validate the initial system

1.  Build the book library, research workflow, core software, golden
    dataset, and evaluation framework.
2.  Use Opus 5.5 during initial development to review the architecture,
    dataset, source evidence, and initial implementation.
3.  Cross-check important cases against books, independent sources, and
    independent calculations.
4.  Freeze and version the approved golden dataset.
5.  Run the initial system with Opus 5.5 against the dataset.
6.  Fix defects and repeat testing until agreed acceptance criteria are
    met.

### Stage B --- Transition to Qwen 3.8

1.  Configure Groq Qwen 3.8 as the candidate runtime model.
2.  Run the same approved evaluation dataset with the same test inputs
    and evaluation criteria.
3.  Compare Qwen results with the benchmark and initial baseline.
4.  Identify failures and tune prompts/configuration or application
    logic as appropriate.
5.  Repeat the evaluation until Qwen meets the agreed acceptance
    criteria.
6.  Record the stable Qwen model and prompt configuration as the
    production baseline.

### Stage C --- Normal operation

-   Qwen is the primary runtime model.
-   Opus is not called for every user query.
-   The evaluation framework remains available for deliberate test runs.
-   Ordinary application use does not trigger the full migration
    evaluation suite.

------------------------------------------------------------------------

## 12. Future model migration procedure

When a future model is considered:

1.  Preserve the current production model, prompts, configuration, and
    evaluation results as the baseline.
2.  Add the candidate model through the provider adapter.
3.  Run the frozen golden dataset against the candidate using the same
    test conditions.
4.  Compare results by tradition and test category.
5.  Review regressions, improvements, unsupported claims, and
    source-fidelity failures.
6.  Tune prompts or configuration if needed.
7.  Re-run the evaluation and record every attempt.
8.  Approve the migration only when acceptance criteria are satisfied.
9.  Retain the prior baseline so the migration can be reversed if
    necessary.

A prompt change that materially changes behaviour should also be
evaluated, even if the underlying model has not changed.

### Evaluation run metadata

Record:

-   Evaluation run ID and date.
-   Dataset version and case IDs.
-   Model provider and exact model ID/version.
-   Prompt and system-instruction version.
-   Application/software commit.
-   Model parameters and relevant configuration.
-   Per-case outputs and scores.
-   Failures, warnings, and aggregate results.
-   Approval decision and reviewer notes.

------------------------------------------------------------------------

## 13. Suggested technology stack

  -----------------------------------------------------------------------
  Area                                Proposed technology
  ----------------------------------- -----------------------------------
  Development assistant               Claude Code

  Backend                             Python and FastAPI

  Frontend                            Next.js and TypeScript

  Database                            PostgreSQL

  Astronomy                           Swiss Ephemeris or another suitable
                                      library, subject to validation and
                                      licensing

  AI runtime                          Groq API, with provider abstraction

  Initial evaluator                   Claude Opus 5.5

  Automated tests                     Pytest and dedicated evaluation
                                      modules

  Frontend tests                      Vitest and suitable browser testing

  Deployment                          Docker

  Version control                     Git
  -----------------------------------------------------------------------

Technology choices should be confirmed during the foundation phase. In
particular, confirm the ephemeris licensing model and the current Groq
model identifier before implementation.

------------------------------------------------------------------------

## 14. Suggested repository structure

``` text
jyotish-platform/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── apps/
│   ├── api/
│   └── web/
├── engine/
│   ├── astronomy/
│   ├── shared_charts/
│   ├── parashari/
│   ├── kp/
│   ├── jaimini/
│   └── integration/
├── knowledge/
│   ├── source_catalog/
│   ├── extracted_text/
│   ├── rules/
│   │   ├── parashari/
│   │   ├── kp/
│   │   └── jaimini/
│   └── research_notes/
├── ai/
│   ├── providers/
│   ├── prompts/
│   ├── research_workflows/
│   └── interpretation/
├── evaluation/
│   ├── datasets/
│   │   ├── astronomy/
│   │   ├── shared_charts/
│   │   ├── parashari/
│   │   ├── kp/
│   │   ├── jaimini/
│   │   ├── interpretation/
│   │   └── integration/
│   ├── evaluators/
│   ├── rubrics/
│   ├── baselines/
│   └── reports/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── research_methodology/
│   └── operations/
└── scripts/
```

This is a proposed structure; it can be refined as the implementation
develops.

------------------------------------------------------------------------

## 15. Development phases and deliverables

  -----------------------------------------------------------------------
  Phase                   Work                    Main deliverable
  ----------------------- ----------------------- -----------------------
  1\. Project foundation  Environment, Git,       Working development
                          architecture,           repository
                          conventions, licensing  
                          investigation           

  2\. Source library      Import, OCR, metadata,  Searchable book library
                          search, source          
                          catalogue               

  3\. Research workflow   Source retrieval, rule  Traceable knowledge
                          records, research       workflow
                          instructions            

  4\. Evaluation          Golden dataset schema,  Working evaluation
  foundation              test runner, reports,   framework
                          versioning              

  5\. Shared astronomy    Time, location,         Tested astronomical
                          ephemeris, ayanamsha,   foundation
                          chart data              

  6\. Parashari engine    Rules, vargas,          Parashari module
                          strengths, Dashas       

  7\. KP engine           Nakshatra/sub-lords,    KP module
                          cusps, significators    

  8\. Jaimini engine      Karakas, aspects,       Jaimini module
                          Argala, Dashas          

  9\. Initial Opus        Review sources,         Initial validation
  validation              datasets, calculations, report
                          implementation          

  10\. Qwen integration   Provider integration    Qwen-powered
                          and runtime prompts     application

  11\. Qwen stabilization Run benchmark, tune,    Stable Qwen
                          rerun, baseline         configuration

  12\. Integrated         Individual,             Multi-system
  interpretation          comparative, combined   interpretation
                          readings                

  13\. Application and    User interface,         Release candidate
  release                 security, deployment,   
                          documentation           
  -----------------------------------------------------------------------

The evaluation framework and golden dataset should be developed early
and expanded throughout the project---not postponed until the end.

------------------------------------------------------------------------

## 16. Acceptance criteria

The project should not be considered ready merely because the
application runs.

### Shared foundation

-   Birth data and time-zone conversion are reproducible.
-   Astronomical calculations pass independent reference tests.
-   Calculation conventions are explicit and recorded.

### Each Jyotish system

-   Supported features have documented specifications.
-   Rules are traceable to sources where applicable.
-   Calculations and boundaries have automated tests.
-   Tradition-specific rules remain isolated.

### Knowledge library

-   Source metadata and page/verse references are maintained.
-   OCR uncertainty is visible.
-   Conflicting interpretations are recorded.

### AI and interpretation

-   Outputs distinguish the three traditions.
-   Classical claims are source-grounded where possible.
-   Unsupported certainty and invented citations are tested for.
-   The system can acknowledge ambiguity and insufficient evidence.

### Evaluation and migration

-   The golden dataset is versioned and reproducible.
-   Tests produce per-case and per-category reports.
-   Model and prompt versions are recorded.
-   Candidate models can be compared against the same benchmark.
-   Migration approval is based on agreed thresholds, not a single
    overall score.

Passing this framework demonstrates consistency with the approved
specifications and reference cases. It does not establish the scientific
validity of astrological predictions.

------------------------------------------------------------------------

## 17. Decisions still to be made

These decisions should be researched and recorded before the relevant
modules are finalized:

1.  Product deployment target: desktop, web application, SaaS, or a
    staged combination.
2.  Ayanamsha policy and supported variants.
3.  Node calculation convention.
4.  House and cusp calculation conventions for each tradition.
5.  KP sub-division precision and boundary handling.
6.  Jaimini Chara Karaka convention and Rahu treatment.
7.  Which Jaimini Dasha systems are in the initial release.
8.  Initial list of divisional charts and Parashari features.
9.  Birth-time uncertainty handling.
10. Supported languages and transliteration conventions.
11. Book collection, file formats, editions, and usage rights.
12. Exact Groq model identifier and API availability.
13. Ephemeris library and licensing decision.
14. Hardware, operating system, and development environment.

Do not silently assume defaults for these decisions. Research options,
document the chosen convention, and add tests for it.

------------------------------------------------------------------------

## 18. Immediate next steps

The first implementation work should be:

1.  Confirm the computer operating system and Claude Code installation
    status.
2.  Confirm the available book formats and begin a source inventory.
3.  Create the Git repository and initial project structure.
4.  Write the project `CLAUDE.md` with the architecture, research rules,
    and development workflow.
5.  Build the source catalogue and book-ingestion workflow.
6.  Define the golden dataset schema and evaluation runner.
7.  Research and decide the shared astronomical conventions before
    implementing chart calculations.

**Overall target:** A modular, source-grounded Parashari + KP + Jaimini
research platform with deterministic calculations, separate
tradition-specific engines, Groq Qwen 3.8 as the intended primary
runtime AI, and a frozen, repeatable evaluation framework for initial
validation and future model migrations.
