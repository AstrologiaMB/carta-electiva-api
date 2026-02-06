# Dockerfile optimizado para Railway - API Carta Electiva
FROM python:3.11-slim

ARG COMMIT_SHA
ENV COMMIT_SHA=$COMMIT_SHA

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port for Fly.io
EXPOSE 8005

# CRITICAL: Uvicorn with Fly.io settings
# Extended timeout for intensive astrological calculations
CMD uvicorn app:app \
    --host 0.0.0.0 \
    --port 8005 \
    --timeout-keep-alive 300 \
    --access-log \
    --log-level info
