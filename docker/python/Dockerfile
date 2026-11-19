# read https://devblogs.microsoft.com/ise/dockerizing-uv/
FROM python:3.12-slim-bookworm AS base

# --- ARGUMENTS ---
ARG UNAME=appuser
ARG UID=1000
ARG GID=1000

# --- SYSTEM SETUP ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    curl \
    git \
    make \
    # PostgreSQL client
    libpq-dev \
    postgresql-client \
    # For image to text or OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # For Pillow (if using ImageField)
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    # For cryptography and SSL
    libffi-dev \
    libssl-dev \
    # For health checks
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


 # --- USER SETUP ---
RUN if ! getent group ${GID} >/dev/null; then \
        groupadd -g ${GID} appgroup; \
    fi && \
    if getent passwd ${UID} >/dev/null; then \
        # if exists we change home folder
        EXISTING_USER=$(getent passwd ${UID} | cut -d: -f1); \
        usermod -d /home/${UNAME} -m ${EXISTING_USER} 2>/dev/null || true; \
    else \
        useradd -l -u ${UID} -g ${GID} -m -d /home/${UNAME} -s /bin/bash ${UNAME}; \
    fi && \
    mkdir -p /home/${UNAME}/.cache/uv && \
    chown -R ${UID}:${GID} /home/${UNAME}

ENV UNAME=$UNAME

# --- ENV & UV SETUP ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    DEBIAN_FRONTEND=noninteractive \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_NO_MANAGED_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"


# Set working directory
WORKDIR /app

RUN chown $UID:$GID /app

# Install uv from official source
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

#############################
# Development
#############################
FROM base AS development

ARG UID
ARG GID
ARG UNAME

USER ${UID}:${GID}

#############################
# Production
#############################
FROM base AS production

ARG UID
ARG GID
ARG UNAME

# Use the non-root user defined in base or here
USER ${UID}:${GID}

# Copy dependency files first
COPY --chown=$UID:$GID uv.lock pyproject.toml /app/


# Install dependencies (Production only: --no-dev, and include production extra)
RUN --mount=type=cache,target=/home/${UNAME}/.cache/uv,uid=$UID,gid=$GID \
    uv sync --frozen --no-install-project --no-dev --extra production

# Copy the application source code
COPY --chown=$UID:$GID . /app

# Production-ready environment variables
ENV DEBUG=False \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Run collectstatic at build time to consolidate assets
# We use a dummy secret key to avoid errors if the real one isn't provided as a build arg
RUN DJANGO_SECRET_KEY=dummy-key-for-build-only \
    DATABASE_NAME=dummy \
    DATABASE_USER=dummy \
    DATABASE_PASSWORD=dummy \
    DATABASE_HOST=dummy \
    DATABASE_PORT=5432 \
    MEDIA_ROOT=/tmp/media \
    REDIS_URL=redis://localhost:6379/0 \
    uv run python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Use Gunicorn for production instead of runserver
# TODO add 'gunicorn' to your pyproject.toml
# , "--workers", "3"
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
