#!/bin/bash
# Setup script for the AI CEO Strategic Intelligence Agent.
#
# Ordering matters here: Python deps install first with fast-fail (set -e),
# then Ollama install/start/pull is fault-tolerant (set +e, || true) so a
# flaky Ollama download doesn't take down the whole environment - you can
# always retry the Ollama steps manually afterwards.

set -e

echo "=== Installing Python dependencies ==="
if command -v uv &> /dev/null; then
    uv sync
else
    pip install -r requirements.txt --break-system-packages
fi

set +e

echo ""
echo "=== Installing Ollama ==="
if command -v ollama &> /dev/null; then
    echo "Ollama already installed, skipping."
else
    curl -fsSL https://ollama.com/install.sh | sh || \
        echo "Ollama install failed - install manually: https://ollama.com/download"
fi

echo ""
echo "=== Starting Ollama server ==="
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

echo ""
OLLAMA_MODEL="${OLLAMA_MODEL:-phi4-mini}"
echo "=== Pulling model: $OLLAMA_MODEL ==="
echo "(phi4-mini is the default - smallest model, best for CPU-only Codespaces."
echo " For better quality with more RAM/GPU, set OLLAMA_MODEL=qwen3:8b or llama3.1:8b)"
ollama pull "$OLLAMA_MODEL" || \
    echo "Model pull failed - run manually: ollama pull $OLLAMA_MODEL"

echo ""
echo "=== Setup complete ==="
echo "Run 'ollama list' to confirm the model is available before running the notebooks."
