FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY logs-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY logs-service/app.py .
COPY logs-service/input_sanitizer.py .

# Copy utils directory for mTLS utilities (if needed in future)
COPY utils /app/utils

# Create certs directory (certificates will be mounted as volume)
RUN mkdir -p /app/certs

# Expose port
EXPOSE 5006

# Use HTTPS with server certificate for mTLS
# Certificates are mounted from docker-compose volume
# Client certificate verification handled via service API key middleware
# Use SSL server wrapper since gunicorn doesn't support SSL natively
ENV HOST=0.0.0.0
ENV PORT=5006
ENV CERTFILE=/app/certs/logs-service-server-cert.pem
ENV KEYFILE=/app/certs/logs-service-key.pem
CMD ["python", "/app/utils/ssl_server.py"]
