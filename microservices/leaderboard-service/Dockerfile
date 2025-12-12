FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ./leaderboard-service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip>=24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./leaderboard-service/ .

# Copy shared utils directory
COPY ./utils /app/utils

# Create non-root user
RUN useradd --create-home --shell /bin/bash leaderuser && \
    chown -R leaderuser:leaderuser /app
USER leaderuser

EXPOSE 5004

CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--workers", "4", "app:app"]