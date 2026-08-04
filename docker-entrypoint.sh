#!/bin/bash
set -e

ollama serve &

echo "Waiting for Ollama to be ready..."
until curl -sf http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done
echo "Ollama ready."

echo "Pulling embeddinggemma (FAQ retrieval always embeds locally)..."
ollama pull embeddinggemma

if [ -z "$OLLAMA_API_KEY" ]; then
  LOCAL_OLLAMA_MODEL="${LOCAL_OLLAMA_MODEL:-llama3.2:3b}"
  echo "No OLLAMA_API_KEY set -- pulling local chat model ($LOCAL_OLLAMA_MODEL)..."
  ollama pull "$LOCAL_OLLAMA_MODEL"
else
  echo "OLLAMA_API_KEY set -- chat will use Ollama Cloud, skipping local chat model pull."
fi

echo "Starting app..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
