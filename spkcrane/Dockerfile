FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080

# Run with gunicorn for production
# - workers=1 because ADK uses in-memory sessions (shared state)
# - timeout=120 to allow slow Gemini API responses
# - threads=4 for concurrent request handling within single worker
CMD exec gunicorn \
    --bind :$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    line_webhook:app
