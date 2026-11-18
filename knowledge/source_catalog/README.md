# Source catalogue

One YAML file per source: `<SOURCE_ID>.yaml` (schema: `knowledge/rulebase/sources.py`, template: `_template.yaml.example`).

**This directory is intentionally empty.** The owner has not confirmed owning any recommended book (Q-014), so no source is catalogued and no book text is ingested. Entries are added only after the owner supplies the inventory. Books, scans and extracted text are never committed (`.gitignore`, CI `scripts/check_repo_files.py`).

Rules cite sources as `SRC-<ID>:<locator>`. `jyotish rules validate` checks that every cited source exists here, and that a VERIFIED rule cites only sources the owner has confirmed (or public-domain ones).
