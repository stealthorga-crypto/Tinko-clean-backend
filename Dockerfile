# Backend Dockerfile for Stealth Recovery
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

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Environment variables (override in docker-compose.yml or deployment)
ENV DATABASE_URL=sqlite:////app/data/stealth_recovery.db
ENV JWT_SECRET=change-me-in-production
ENV JWT_ALGORITHM=HS256
ENV JWT_EXPIRY_MINUTES=1440

# Run migrations on startup, then start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
