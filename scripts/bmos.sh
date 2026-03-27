#!/bin/bash
set -x
exec 1> >(tee -a /home/pi/bmos_startup.log) 2>&1

echo "=== BMO Starting $(date) ==="

export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000

echo "Initializing hardware..."
/home/pi/bmos/scripts/armsinit.sh
/home/pi/bmos/scripts/armsdown.sh &

# Kill feh splash screen before playing video
killall feh 2>/dev/null

echo "Playing intro..."
mpv --fs --ontop --quiet --really-quiet --no-input-default-bindings --no-osd-bar --osd-level=0 --volume=50 /home/pi/bmos/videos/intro.mp4 &

sleep 5.5

echo "Starting BMO..."
cd /home/pi/bmos/
./bmos
