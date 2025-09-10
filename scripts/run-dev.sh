#!/bin/bash
# Development Environment Runner

echo "🔧 Starting Weather API in DEVELOPMENT mode..."

# Load development environment
export ENV_FILE=.env.dev
if [ -f "$ENV_FILE" ]; then
    echo "📄 Loading environment from $ENV_FILE"
    set -a
    source $ENV_FILE
    set +a
else
    echo "❌ Environment file $ENV_FILE not found"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "weather-env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv weather-env
fi

echo "📦 Activating virtual environment..."
source weather-env/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

echo "🚀 Starting development server with hot reload..."
uvicorn app.core.main:app --reload --host $HOST --port $PORT --log-level debug

