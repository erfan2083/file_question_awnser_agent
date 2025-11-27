# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Copy source code (needed for hatchling to build the package)
COPY api ./api
COPY chat ./chat
COPY config ./config
COPY core ./core
COPY documents ./documents
COPY evaluation ./evaluation
COPY rag ./rag
COPY manage.py .

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Copy remaining project files
COPY . .

# Collect static files (if needed)
RUN uv run python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run Django development server
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
