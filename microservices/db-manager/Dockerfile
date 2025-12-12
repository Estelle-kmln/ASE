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

# Create non-root user
RUN useradd --create-home --shell /bin/bash authuser && \
    chown -R authuser:authuser /app
USER authuser

# Port for the db-manager sevice
EXPOSE 5005

CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "4", "app:app"]
