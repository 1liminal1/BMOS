#!/bin/bash

LOG_FILE="/home/pi/bmos/bmos_error.log"

echo "Starting google-voice.sh $(date)" >> "$LOG_FILE"

python3 /home/pi/bmos/gv/transcribe.py 2>> "$LOG_FILE"
