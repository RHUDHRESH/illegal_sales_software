#!/bin/bash

# Raptorflow Lead Engine - Development Startup

echo "🚀 Raptorflow Lead Engine - Starting..."
echo ""

# Check Python
python_cmd=$(which python3 || which python)
if [ -z "$python_cmd" ]; then
    echo "❌ Python not found. Install Python 3.9+ first."
    exit 1
fi
echo "✅ Python: $python_cmd"

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $python_cmd -m venv venv
fi

# Activate venv
echo "🔌 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check Ollama
echo ""
echo "📡 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not running at http://localhost:11434"
    echo "   Start Ollama first:"
    echo "   - Mac/Linux: ollama serve"
    echo "   - Windows: ollama serve (in cmd/PowerShell)"
    echo "   Then re-run this script."
    exit 1
fi
echo "✅ Ollama is running"

# Check models
echo "📦 Checking Ollama models..."
models=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' || echo "")
if ! echo "$models" | grep -q "gemma3:1b"; then
    echo "⚠️  gemma3:1b not found. Pulling (this may take a few minutes)..."
    curl -X POST http://localhost:11434/api/pull -d '{"name":"gemma3:1b"}' || true
fi
if ! echo "$models" | grep -q "gemma3:4b"; then
    echo "⚠️  gemma3:4b not found. Pulling (this may take a few minutes)..."
    curl -X POST http://localhost:11434/api/pull -d '{"name":"gemma3:4b"}' || true
fi

# Start API
echo ""
echo "🎯 Starting FastAPI server on http://127.0.0.1:8000"
echo "📚 Docs at http://127.0.0.1:8000/docs"
echo ""
uvicorn main:app --reload --host 127.0.0.1 --port 8000
