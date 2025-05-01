# Stage 1: Builder for compiling dependencies
FROM alpine:latest AS builder
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev

# Install runtime dependencies
RUN apk add --no-cache libpq

# Configure pip and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM alpine:latest
WORKDIR /app

# Runtime environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=tastify.settings

# Create non-root user first
RUN adduser -D appuser

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code with proper exclusions
COPY . .
RUN find . -type d \( -name __pycache__ -o -name .git -o -name venv \) -prune -exec rm -rf {} \; || true

# Create static directory and set up static files
RUN mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app/staticfiles

# Set proper permissions
RUN chown -R appuser:appuser /app && \
    chmod +x /usr/local/bin/gunicorn

# Switch to non-root user
USER appuser

# Port and healthcheck configuration
EXPOSE 80

# Gunicorn execution with production settings
CMD ["gunicorn", "--bind", "0.0.0.0:80", \
     "--workers", "3", \
     "--log-level", "info", \
     "tastify.wsgi:application"]

