FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY auth-service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY auth-service/ .

# Copy utils directory for mTLS utilities (if needed in future)
COPY utils /app/utils

# Create certs directory (certificates will be mounted as volume)
RUN mkdir -p /app/certs

# Create non-root user
RUN useradd --create-home --shell /bin/bash authuser && \
    chown -R authuser:authuser /app
USER authuser

EXPOSE 5001

# Use HTTPS with server certificate for mTLS
# Certificates are mounted from docker-compose volume
# Client certificate verification handled via service API key middleware
# Use SSL server wrapper since gunicorn doesn't support SSL natively
ENV HOST=0.0.0.0
ENV PORT=5001
ENV CERTFILE=/app/certs/auth-service-server-cert.pem
ENV KEYFILE=/app/certs/auth-service-key.pem
CMD ["python", "/app/utils/ssl_server.py"]