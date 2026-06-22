#!/bin/bash

set -e

echo "=== Installing Python dependencies ==="

if command -v uv &> /dev/null; then
    echo "Using uv"

    # create environment outside workspace
    uv venv /tmp/aiceo-venv

    source /tmp/aiceo-venv/bin/activate

    # install only requirements.txt
    uv pip install -r requirements.txt

else
    pip install -r requirements.txt --break-system-packages
fi


set +e

echo ""
echo "=== Installing Ollama ==="

if command -v ollama &> /dev/null; then
    echo "Ollama already installed"
else
    curl -fsSL https://ollama.com/install.sh | sh
fi


echo ""
echo "=== Starting Ollama ==="

ollama serve > /tmp/ollama.log 2>&1 &

sleep 3


OLLAMA_MODEL="${OLLAMA_MODEL:-phi4-mini}"

echo "Pulling $OLLAMA_MODEL"

ollama pull "$OLLAMA_MODEL"


echo ""
echo "=== Setup complete ==="