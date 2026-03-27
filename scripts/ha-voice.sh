#!/bin/bash
# BMOS Voice Processing with HA WebSocket Pipeline and Google Fallback
# Tries Home Assistant WebSocket Pipeline first, falls back to Google Speech Recognition if HA unavailable

# Try HA WebSocket Pipeline first (uses BMOpi assistant with BMO voice)
python3 /home/pi/bmos/ha/ha_assist_ws.py

# If HA failed (exit code 1), fall back to Google
if [ $? -ne 0 ]; then
    echo "HA Pipeline unavailable, falling back to Google Speech Recognition" >&2
    python3 /home/pi/bmos/gv/transcribe.py
fi
