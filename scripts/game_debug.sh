#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p /home/pi/game_logs

# Log file with timestamp
LOG_FILE="/home/pi/game_logs/game_launch_$(date +%Y%m%d_%H%M%S).log"

# Log system info
echo "=== System Info ===" > "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
uname -a >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Log display info
echo "=== Display Info ===" >> "$LOG_FILE"
echo "DISPLAY=$DISPLAY" >> "$LOG_FILE"
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE" >> "$LOG_FILE"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Try to launch game with debug output
echo "=== Launch Attempt ===" >> "$LOG_FILE"
/opt/retropie/emulators/retroarch/bin/retroarch -v -L /opt/retropie/libretrocores/lr-fceumm/fceumm_libretro.so --config /opt/retropie/configs/nes/retroarch.cfg "$1" 2>&1 | tee -a "$LOG_FILE"
