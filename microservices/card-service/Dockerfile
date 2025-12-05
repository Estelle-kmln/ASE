FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy shared common modules into container
COPY common /app/common

# Add shared code directory to Python path (used by all services for db_manager, utils, etc.)
ENV PYTHONPATH="/app:/app/common"

# Create non-root user
RUN useradd --create-home --shell /bin/bash carduser && \
    chown -R carduser:carduser /app
USER carduser

EXPOSE 5002

CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "4", "app:app"]