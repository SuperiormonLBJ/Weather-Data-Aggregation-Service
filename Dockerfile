# Multi-stage build for optimal image size
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code and health check script
COPY app/ ./app/
COPY healthcheck.py ./
COPY .env ./

# Make health check script executable
RUN chmod +x healthcheck.py

# Add Python user packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 healthcheck.py || exit 1

# Run the application
CMD ["uvicorn", "app.core.main:app", "--host", "0.0.0.0", "--port", "8000"] 