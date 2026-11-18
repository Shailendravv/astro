"""Pure calculation engine: no I/O, no DB, no network, no LLM, no global state.

Tradition packages (parashari, kp, jaimini) never import each other (import-linter, D-021).
"""

from typing import Final

# Bumped on any output-affecting change (docs/architecture.md section 7). Stored with every chart.
ENGINE_VERSION: Final = "0.1.0"
