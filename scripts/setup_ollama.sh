#!/bin/bash

# Setup Ollama for local LLM processing

echo "Setting up Ollama for local LLM processing..."

# Check OS type
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS. Installing Ollama..."
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama via brew..."
        brew install ollama
    else
        echo "Ollama already installed."
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux. Installing Ollama..."
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "Ollama already installed."
    fi
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &

# Wait for service to start
sleep 5

# Pull recommended models
echo "Pulling recommended models..."
ollama pull llama3
ollama pull mistral
ollama pull codellama

echo "Ollama setup complete!"
echo "Available models:"
ollama list

echo ""
echo "To use Ollama in the system, add this to your .env file:"
echo "OLLAMA_API_BASE=http://localhost:11434"
echo ""
echo "To test Ollama:"
echo "curl http://localhost:11434/api/generate -d '{"model": "llama3", "prompt": "Hello"}'"