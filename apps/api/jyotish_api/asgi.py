"""ASGI entry point: `uvicorn jyotish_api.asgi:app`. Settings come from the environment only."""

from jyotish_api.config import Settings
from jyotish_api.main import create_app

# All values are read from the environment; a missing one raises at startup (no silent defaults).
app = create_app(Settings())
