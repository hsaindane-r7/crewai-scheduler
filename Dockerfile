FROM python:3.13-slim AS base

# Prevents Python from writing pyc files, which is like a shortcut, but as container is temporary, we just rebuild the image
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
# makes sure logs appear immediately and dont wait in a buffer so that we can see what went wrong if container crashed. 

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no venv needed inside container)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY *.py ./

# Sync again to install the project itself
RUN uv sync --frozen --no-dev

# Default command - can be overridden at runtime
ENTRYPOINT ["uv", "run", "python", "main.py"]

# Default args (user can override)
CMD ["--help"]

