# Dockerfile optimizado para Railway - API Carta Electiva
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port (documentación, Railway ignora esto)
EXPOSE 8080

# CRITICAL: Uvicorn con configuración optimizada para Railway
# Timeout extendido para cálculos astrológicos intensivos
CMD uvicorn app:app \
    --host 0.0.0.0 \
    --port $PORT \
    --timeout-keep-alive 300 \
    --access-log \
    --log-level info
