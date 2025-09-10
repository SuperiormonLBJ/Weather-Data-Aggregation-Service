#!/bin/bash
# UAT Environment Runner

echo "🧪 Starting Weather API in UAT mode..."

# Load UAT environment
export ENV_FILE=.env.uat
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

echo "🚀 Starting UAT server..."
uvicorn app.core.main:app --host $HOST --port $PORT --workers 2

