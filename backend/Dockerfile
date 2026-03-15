# --- Frontend build stage (optional) ---
FROM node:18-alpine AS frontend-builder
WORKDIR /build

# copy frontend when available (supports two possible frontend layouts)
COPY frontend/package*.json ./


# Install dependencies and build the main frontend if present
RUN if [ -f package.json ]; then npm ci || true; fi
COPY frontend .
RUN if [ -f package.json ]; then npm run build || true; fi

# --- Python runtime stage ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy built frontend assets from the frontend-builder stage (if any)
COPY --from=frontend-builder /build/dist /app/frontend_dist

# Create logs directory
RUN mkdir -p logs && chmod 755 logs

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with gunicorn in production
CMD ["gunicorn", "main:app", "--workers=4", "--worker-class=uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000", "--access-logfile=-", "--error-logfile=-"]
