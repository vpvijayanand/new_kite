# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_APP=run.py

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    libffi-dev \
    libssl-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r flaskapp && useradd -r -g flaskapp flaskapp

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/storage/logs /app/storage/tokens /app/storage && \
    chown -R flaskapp:flaskapp /app

# Copy application code
COPY . .

# Set proper permissions for the app directory
RUN chown -R flaskapp:flaskapp /app

# Switch to non-root user
USER flaskapp

# Copy and setup entrypoint script
USER root
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
    apt-get update && apt-get install -y netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*
USER flaskapp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
ENTRYPOINT ["/entrypoint.sh"]
