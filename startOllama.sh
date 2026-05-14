#!/bin/bash

ollama serve &
echo "Waiting for Ollama..."
until ollama list > /dev/null 2>&1; do
    sleep 1
done
echo "This is not sus"
ollama pull gemma4:e2b
echo "Gemma4:e2b ready to use"
wait