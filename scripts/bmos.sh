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

echo "Playing intro..."
omxplayer --aspect-mode fill -o alsa --no-keys --no-osd /home/pi/bmos/videos/intro.mp4 &

sleep 3.5

echo "Starting BMO..."
cd /home/pi/bmos/
./bmos
