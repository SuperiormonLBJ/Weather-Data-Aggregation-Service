#!/bin/bash
# Production Environment Runner

echo "🚀 Starting Weather API in PRODUCTION mode..."

# Load production environment
export ENV_FILE=.env.prod
if [ -f "$ENV_FILE" ]; then
    echo "📄 Loading environment from $ENV_FILE"
    set -a
    source $ENV_FILE
    set +a
else
    echo "❌ Environment file $ENV_FILE not found"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo "🚀 Starting production server with optimized settings..."
# Use gunicorn for production with 4 workers
gunicorn app.core.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind $HOST:$PORT \
    --log-level warning \
    --timeout 30

