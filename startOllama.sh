#!/bin/bash

ollama serve &
sleep 10
echo "This is a prank"
ollama pull gemma4:e2b
echo "Doomsday device ready"
echo "Executing doommsday device"
echo "Gemma4:e2b ready to use"
wait