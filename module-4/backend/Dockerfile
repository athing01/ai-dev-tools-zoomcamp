# Multi-stage build for backend
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY taskflow_backend/ ./taskflow_backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create virtual environment and install dependencies
RUN uv sync --frozen

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy everything from builder
COPY --from=builder --chown=appuser:appuser /app ./

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "taskflow_backend.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]