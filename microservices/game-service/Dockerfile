FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY game-service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY game-service/ .

# Copy utils directory for mTLS utilities
COPY utils /app/utils

# Create certs directory (certificates will be mounted as volume)
RUN mkdir -p /app/certs

# Create non-root user
RUN useradd --create-home --shell /bin/bash gameuser && \
    chown -R gameuser:gameuser /app
USER gameuser

EXPOSE 5003

# Use HTTPS with server certificate for mTLS
# Certificates are mounted from docker-compose volume
# Client certificate verification handled via service API key middleware
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "4", "--certfile", "/app/certs/game-service-server-cert.pem", "--keyfile", "/app/certs/game-service-key.pem", "app:app"]