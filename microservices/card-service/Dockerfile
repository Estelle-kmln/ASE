FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY card-service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY card-service/ .

# Copy utils directory for mTLS utilities
COPY utils /app/utils

# Create certs directory (certificates will be mounted as volume)
RUN mkdir -p /app/certs

# Create non-root user
RUN useradd --create-home --shell /bin/bash carduser && \
    chown -R carduser:carduser /app
USER carduser

EXPOSE 5002

# Use HTTPS with server certificate for mTLS
# Certificates are mounted from docker-compose volume
# Client certificate verification handled via service API key middleware
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "4", "--certfile", "/app/certs/card-service-server-cert.pem", "--keyfile", "/app/certs/card-service-key.pem", "app:app"]