# API image. Build context is the repository root (it needs engine/, ai/, evaluation/ and apps/api/).
#   docker compose build api
# Base images are referenced by tag here; pin them by digest before release (docs/security.md section 2).
FROM python:3.12-slim

# uv is copied from its official image at a pinned version.
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY engine ./engine
COPY ai ./ai
COPY evaluation ./evaluation
COPY apps/api ./apps/api
# Production dependencies only, from the lockfile, with the project installed as a real package.
RUN uv sync --frozen --no-dev --no-editable

ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=${GIT_COMMIT} \
    PATH="/app/.venv/bin:${PATH}"

RUN useradd --system --no-create-home --uid 10001 jyotish
USER jyotish

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4).status == 200 else 1)"

# Inside the container uvicorn must listen on all interfaces; the host side is bound to 127.0.0.1
# in docker-compose.yml.
CMD ["uvicorn", "jyotish_api.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
