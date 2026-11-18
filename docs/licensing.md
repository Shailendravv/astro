# Licensing & Copyright Memo — Jyotish Research Platform

> Status: DRAFT v0.1 (2026-11-18), task T1.8. Related: [decisions.md](decisions.md) D-011, D-013, D-015; [security.md](security.md) §7; [architecture.md](architecture.md) §6.
> **This is a working memo, not legal advice.** It records what was checked, what was not, and what must be re-checked before the project is ever shared or hosted.

## 1. What was verified and what was not

| Item | How it was checked | Confidence |
|---|---|---|
| Declared licences of every installed Python and npm package | Scripted scan of package metadata on 2026-11-18 (§3) | The licence **declared by the package**. Licence texts were not read |
| Swiss Ephemeris, GeoNames, Skyfield/JPL terms | Taken from the project docs (D-013, D-015, security.md §7). **Not re-read from the original licence pages in this session** | Must be re-checked at M4, before `pyswisseph` or any ephemeris file is added |
| Copyright status of any book | Not assessed. No book inventory exists (Q-014, Q-015) | n/a |
| Qwen model licence and Groq API terms | Not reviewed. Groq's data-retention facts are recorded in D-012 | Review before any redistribution of model output |

## 2. Swiss Ephemeris (the main licensing decision)

- **Position in the docs (D-013, PROPOSED):** use Swiss Ephemeris through `pyswisseph` under **AGPL-3.0** for local personal use, with a **Swiss Ephemeris professional licence** as the alternative if the software is ever distributed or offered as a service.
- **State today:** **not installed, not imported.** Nothing in the repository depends on it yet. `pyswisseph` and the `.se1` data files are first needed in M4 (T4.3).
- **Why it matters:** the AGPL is a strong copyleft licence that also covers use over a network. For one person running the app on their own machine nothing is distributed, so no source-release obligation arises (D-001). That stops being true if the code or an image containing it is **given to anyone**, or if other people use the app over a network.
- **Gate before M4 work starts:**
  1. The owner confirms D-013 (it is still PROPOSED).
  2. Claude Code re-reads the current Swiss Ephemeris licence terms from Astrodienst's official pages and records the date and URL here.
  3. The repository stays **private** (D-024). Publishing it publicly would make the AGPL source obligation immediate for the combined work.
- **Fallback if the owner does not want AGPL exposure:** buy the professional licence, or replace the ephemeris layer (Skyfield/JPL could provide positions but not Indian ayanamsha or house code, so this is a large change). Either choice needs a new decision entry.

## 3. Dependencies installed in M1 (scan of 2026-11-18)

**Python (67 packages, runtime and dev, including this project itself, which declares no licence):** MIT (34), BSD-2/3-Clause (13), Apache-2.0 (11), MPL-2.0 (3), PSF (2), Apache-2.0-or-BSD-2-Clause (1), **LGPL-3.0-only (2)**. No AGPL or GPL.
**npm (production tree of `apps/web`, 37 packages):** MIT (28), Apache-2.0 or Apache-2.0 AND MIT (6), BSD-3-Clause (1), 0BSD (1), and one `Apache-2.0 AND LGPL-3.0-or-later AND MIT` package. No AGPL or GPL.

| Component | Licence (as declared) | Used for | Note |
|---|---|---|---|
| `psycopg`, `psycopg-binary` | LGPL-3.0-only | API database driver (runtime) | Used unmodified as a normal dependency. Fine for private local use. If the Docker image is ever distributed, ship the licence notice and keep the library replaceable |
| `@img/sharp-wasm32` (via Next.js image support) | Apache-2.0 AND LGPL-3.0-or-later AND MIT | Optional image optimisation in Next.js | Not used by this app's pages. Same distribution note as above |
| `hypothesis` | MPL-2.0 | Property tests (dev only) | File-level copyleft; unmodified; not shipped in images |
| `certifi`, `pathspec` | MPL-2.0 | Transitive | Unmodified |
| Everything else | MIT / BSD / Apache-2.0 / PSF / 0BSD | Runtime and tooling | Permissive; keep attribution notices if distributed |
| PostgreSQL 17, `pgvector` image | PostgreSQL licence (not scanned; official images) | Database container | Pull from the official image; re-check when pinning digests |
| Next.js, React, FastAPI, Pydantic, SQLAlchemy, Vitest, Playwright | MIT or Apache-2.0 as declared | App and tests | |

The project's own code has **no licence file yet**: by default all rights are reserved. Choose a licence only when the owner decides to share it, and only after §2 is settled.

## 4. GeoNames (T4.2, not yet used)

GeoNames data is published under CC BY 4.0 (D-015). When `cities500` is imported (M4), the About page must credit GeoNames, and the import script must record the dataset version. The raw data file is large and is fetched by a script, not committed.

## 5. JPL ephemerides and Skyfield (tests only, M4)

D-013 plans Skyfield with JPL DE440/441 as an independent reference in tests, never at runtime. Their licences have **not** been checked in this session. Check them when they are added, record the result here, and keep the large data files out of git (the `.gitignore` already excludes `*.bsp`).

## 6. Books and other copyrighted text

The rules live in [decisions.md](decisions.md) D-011 (copy rules and per-source procedure) and [security.md](security.md) §7. Summary of what is enforced mechanically as of M1:

- `.gitignore` excludes PDFs, e-books, scans, `library/`, `JyotishLibrary/`, and everything under `knowledge/extracted_text/`.
- CI runs `scripts/check_repo_files.py`, which fails on a book/scan file, an `.env` file, or a binary larger than 1 MB, in tracked or untracked files.
- Library files will live outside the repository (PROPOSED `D:\JyotishLibrary\`) and be mounted read-only.
- **No book is assumed to be owned** (owner decision on Q-014, 2026-11-18). Per-source copyright status (Q-015) cannot start until the owner supplies the inventory. Until then no named book is ingested, and tests use synthetic or public-domain documents only.
- Excerpts sent to the AI provider stay capped (security.md §4).

## 7. Qwen model and Groq API

- The runtime model and the Groq API terms govern what may be done with generated readings. **Not yet reviewed.** Review the Qwen model licence and Groq's terms before sharing readings outside the owner's personal use.
- Provider retention facts (including the optional Zero Data Retention setting) are in D-012 and [security.md](security.md) §4.

## 8. When to revisit this memo

- Before `pyswisseph` or any `.se1` file is added (M4).
- Before the repository is made public, shared, or mirrored anywhere.
- Before building or sharing a Docker image outside the owner's machine.
- Before D-001 changes (any user other than the owner).
- Before any book-derived text, rule quotation, or screenshot is shown to another person.
