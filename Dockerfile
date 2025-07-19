# Multi-stage Docker build for Monitoring Dashboard
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# Add metadata
LABEL maintainer="AI Trading Machine Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.version=$VERSION \
      org.label-schema.name="monitoring-dashboard" \
      org.label-schema.description="Real-time trading monitoring dashboard for production deployment"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash monitor && \
    mkdir -p /app/static /app/templates /app/logs && \
    chown -R monitor:monitor /app

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Set ownership to non-root user
RUN chown -R monitor:monitor /app

# Switch to non-root user
USER monitor

# Health check for dashboard availability
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Environment variables for production
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=8080

# Expose port for dashboard
EXPOSE 8080

# Default command for production
CMD ["python", "-m", "monitoring_dashboard.main"]
