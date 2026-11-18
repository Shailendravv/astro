# Security & Privacy — Jyotish Research Platform

> Status: DRAFT v0.1 (2026-11-17). Release 1 is a **single-user, local** application (D-001). This document covers that setup and the changes needed before any multi-user or hosted deployment.
> Related: [deployment.md](deployment.md), [api.md](api.md) §2.

## 1. What we protect

| Asset | Sensitivity | Why |
|---|---|---|
| Birth records (date, time, place, labels/names) | **High (personal data)** | Identifies people; birth date + place is sensitive personal data, especially for family members or others |
| Readings and questions | High | May reveal health, relationship, career concerns |
| API keys (Groq; no Anthropic key, D-030) | High | Billing abuse |
| Book library (scans, extracted text) | Medium–High (copyright) | Owned copies for personal use; must not be redistributed |
| Rules, golden dataset, evaluation results | Medium (integrity) | Corruption silently breaks correctness |
| Source code | Low–Medium | Swiss Ephemeris AGPL obligations if distributed |

## 2. Threat model (release 1)

| Threat | Mitigation |
|---|---|
| Another device on the LAN reaches the API/DB | Bind `api`, `web` to `127.0.0.1`; do not publish the `db` port; Windows firewall default deny inbound |
| Malicious website calls the local API from the browser (CSRF / DNS rebinding) | Strict CORS (only `http://127.0.0.1:3000`); reject requests whose `Host` header is not `127.0.0.1`/`localhost`; JSON-only bodies; no cookies used for auth |
| Secrets committed to git | `.env` git-ignored; `.env.example` with placeholders; pre-commit secret scan (gitleaks) |
| Birth data sent to LLM providers | Data minimization (§4) |
| Books leaked via git push | Library root outside the repo; `.gitignore` guards; CI check that no PDF/image > 1 MB is committed |
| Prompt injection via OCR text or user question | Passages wrapped as quoted data in prompts; structured output + validator; model has no tools or actions in runtime readings |
| Tampering with frozen dataset / baselines | Content hashes; CI fails if frozen files change; DB triggers block updates |
| Laptop theft | OS disk encryption (BitLocker); backups encrypted (§6) |
| Vulnerable dependencies | Lockfiles; Dependabot/`pip-audit`/`npm audit` in CI; pin Docker base image digests |

**Observed on the owner's machine (2026-11-18, T1.1):** a separate Windows service `postgresql-x64-17` (not part of this project) listens on port 5432 on **all interfaces** (`0.0.0.0` and `::`). The project's own database container publishes no port, so this is outside our control and outside the project. Whether it is reachable from the LAN depends on the Windows firewall and that server's `pg_hba.conf`. The owner may want to check or stop it if it is not needed. It is also the reason the project never publishes the DB port.

## 3. Authentication, roles, permissions

**Release 1:** no login. The single local user is implicitly `owner`. Protection comes from network isolation (§2).

**Before any multi-user or hosted deployment (blocking):**

- OIDC authentication; short-lived bearer tokens.
- Roles: `owner` (everything), `reviewer` (read charts they are given, review rules/cases, no settings/keys), `viewer` (read-only assigned readings).
- Per-record ownership and sharing; audit log of reads and writes on birth records.
- Re-run this document as a full threat model.

## 4. Data sent to external services

The only external service that receives data at runtime is the **LLM provider, Groq** (D-030; no Anthropic model is used). Geocoding and OCR are offline.

**Groq retention facts (recorded 2026-11-18 from Groq's "Your Data" page; see D-012):** inference requests are not retained by default; inputs and outputs may be logged for up to 30 days only to troubleshoot reliability or investigate abuse; Zero Data Retention can be enabled in the Groq console Data Controls; retained data is stored in the United States. **Whether ZDR is enabled on the owner's account is UNCONFIRMED** (owner, 2026-11-18; Q-019). It is **not assumed to be enabled.** When the owner confirms, record the date and the Data Controls setting here.

### While ZDR is UNCONFIRMED (precautions in force from 2026-11-18)

1. Treat every provider request and response as retained by Groq for up to 30 days in the United States.
2. **No real person's birth data or chart facts, and no real personal question, goes into any provider request.** Evaluation runs, tests and development use synthetic charts only ([testing.md](testing.md) §5). A reading of the owner's own chart stays blocked until ZDR is confirmed or the owner accepts the residual risk in writing in decisions.md (D-027).
3. `PayloadMinimiser` is mandatory and snapshot-tested before any real call. The judge model's inputs (the reading under test, the rubric) follow the same rules, because a judge call is also a provider call.
4. Book passages are sent only within the caps in this section, and only passages whose rights record permits it (D-011).
5. Recommended, owner's choice: set a spend limit in the Groq console, and keep the API key only in the local `.env`.

### Gate: first real (non-fake) model call

No real call is made, by code, tests, or Claude Code, until **all** of these are recorded as approved by the owner in decisions.md:

- [ ] Provider configuration: provider, the model ID still listed by Groq on that day (Preview model, Q-019), and the thinking vs instruct mode (open).
- [ ] Data handling: ZDR status confirmed, or the owner's written acceptance of the residual risk, plus the precautions above.
- [ ] Spend: the owner's go-ahead for the cost of that run ([deployment.md](deployment.md) §3 "Never in CI").
- [ ] The payload snapshot tests pass for the request type about to be sent.

Until then `RUNTIME_PROVIDER` and `RUNTIME_MODEL_ID` stay **empty** in the local `.env`, and the app reports AI features as off.

Note: exact planetary positions could in principle be used to reconstruct the birth moment. Minimization lowers the exposure; it does not anonymize the data. Treat provider traffic as personal data.

**Sent to LLM providers:**

- Computed **categorical** chart facts (sign, house, nakshatra, pada, lords, sub-lords, karakas, yogas, dasha lords) by `fact_id`, produced by `PayloadMinimiser` (D-027).
- Degrees only where interpretation needs them, rounded (PROPOSED: whole degree, Q-011); boundary proximity as a flag only.
- Retrieved rule records and short source passages relevant to the question.
- The user's question text.
- Language and mode instructions.

**Never sent:**

- Record label or name, birthplace name, coordinates, raw birth date/time.
- Full-precision longitudes, cusp degrees, ayanamsha values, birth-date dasha balance, chart/database IDs.
- Dasha periods outside the question's time window. Those inside it are sent at month precision (PROPOSED, Q-011). Owner may disable timing questions per reading.

**Privacy risks of position data (D-027):** the set of planetary positions narrows the birth date; the ascendant (≈1° per 4 minutes) narrows the birth time; date + time + ascendant/cusps can narrow the birthplace. Rounding and categorical facts reduce this precision but **do not anonymise**. The residual risk is accepted for personal use under D-001 and must be re-assessed before any multi-user use. Evaluation runs use synthetic charts only.

- Whole books or large excerpts. Retrieval sends only the passages needed, each capped (PROPOSED ≤ 1,500 characters per passage, ≤ 12 passages).

A test enforces this ([testing.md](testing.md) §3).

**Provider policies:** before activating a provider, record its data-retention and training policy for API traffic in [decisions.md](decisions.md). Prefer settings that disable retention or training where offered.

## 5. Secrets

| Variable | Used by | Storage |
|---|---|---|
| `GROQ_API_KEY` | ai/providers | `.env` |
| `POSTGRES_PASSWORD` | db, api | `.env`, random 32+ chars generated at setup |
| `BACKUP_PASSPHRASE` | backup script | Windows Credential Manager or password manager; not in `.env` |

- The UI shows only whether a key is set and its last 4 characters.
- Logs never include keys, prompts containing passages, or birth data (structured logging with an allowlist of fields).
- Rotate keys if a leak is suspected. The steps are documented in [deployment.md](deployment.md).

## 6. Personal data handling

- **Purpose:** personal research by the owner.
- **Retention:** kept until the owner deletes them. Delete cascades to charts, readings, and cached results (US-1002) and is hard delete, not just a flag, after a short undo window (PROPOSED 7 days).
- **Backups:** encrypted (age or 7-Zip AES-256 with `BACKUP_PASSPHRASE`). Backups older than the retention window still hold deleted data, so this is documented for the owner.
- **Test data:** synthetic only in the repo ([testing.md](testing.md) §5).
- **Other people's data:** if the owner enters charts of family or friends, they should have their consent.

## 7. Compliance notes

- **India DPDP Act 2023:** processing for purely personal or domestic purposes is out of scope. If the platform is later used for clients or offered as a service, the owner becomes a Data Fiduciary: consent notices, purpose limitation, deletion on request, breach reporting, and possibly cross-border transfer considerations for LLM APIs. Re-assess before D-001 changes.
- **GDPR:** relevant only if EU residents' data is processed in a future service.
- **Copyright:** books are owned copies for personal research. Do not publish extracted text, do not include books in git or Docker images, and record `rights` per source.
- **Swiss Ephemeris AGPL-3.0:** local personal use creates no distribution obligation. Any distribution or network service requires releasing source under AGPL or buying the professional licence (D-013).
- **GeoNames:** CC-BY 4.0, so attribution goes in the About page.
- **Disclaimer:** UI and exports state that readings are interpretations under named traditions and are not scientific predictions or professional advice (plan §16).

## 8. Release security checklist

- [ ] `docker compose ps` shows no ports bound to `0.0.0.0`.
- [ ] Host-header and CORS checks verified by integration test.
- [ ] gitleaks clean on full history.
- [ ] No books, scans, or real birth data in git history.
- [ ] `pip-audit` and `npm audit` show no high/critical issues (or documented exceptions). **Open exception (added 2026-11-18, review by 2026-12-18):** `picomatch` ReDoS (GHSA-fc5q-39xc-vjpf), no patched release exists, dev/build tooling only. Recorded with its reason in `apps/web/audit-exceptions.json`; re-check at the review date.
- [ ] Data-minimization test passes.
- [ ] Backup encryption and restore verified.
- [ ] Provider retention/training settings recorded.
