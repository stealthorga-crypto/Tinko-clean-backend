# Backend Dockerfile for Tinko
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Expose FastAPI port
EXPOSE 8000

# IMPORTANT:
# Do NOT set DATABASE_URL here.
# Railway will inject the correct Postgres URL automatically.
# Removing SQLite override fixed DB mismatch + migration failures.

# Run migrations on startup, then launch the server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
