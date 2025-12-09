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

# Copy application code (from game-service folder)
COPY game-service/app.py .
COPY game-service/input_sanitizer.py .
COPY game-service/security.py .

# Copy shared common modules into container
COPY common /app/common

# Copy utils for all services
COPY utils /app/utils

# Add shared code directory to Python path (used by all services for db_manager, utils, etc.)
ENV PYTHONPATH="/app:/app/common"

# Create non-root user
RUN useradd --create-home --shell /bin/bash gameuser && \
    chown -R gameuser:gameuser /app
USER gameuser

EXPOSE 5003

CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "4", "app:app"]