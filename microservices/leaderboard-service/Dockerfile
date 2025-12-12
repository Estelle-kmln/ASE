FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY leaderboard-service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY leaderboard-service/ .

# Copy utils directory for mTLS utilities (if needed in future)
COPY utils /app/utils

# Create certs directory (certificates will be mounted as volume)
RUN mkdir -p /app/certs

# Create non-root user
RUN useradd --create-home --shell /bin/bash leaderuser && \
    chown -R leaderuser:leaderuser /app
USER leaderuser

EXPOSE 5004

# Use HTTPS with server certificate for mTLS
# Certificates are mounted from docker-compose volume
# Client certificate verification handled via service API key middleware
# Use SSL server wrapper since gunicorn doesn't support SSL natively
ENV HOST=0.0.0.0
ENV PORT=5004
ENV CERTFILE=/app/certs/leaderboard-service-server-cert.pem
ENV KEYFILE=/app/certs/leaderboard-service-key.pem
CMD ["python", "/app/utils/ssl_server.py"]