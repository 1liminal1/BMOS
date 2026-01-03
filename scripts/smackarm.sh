#!/bin/bash
# Start video first but in background
/usr/bin/omxplayer --aspect-mode fill --layer 10010 -o alsa --no-keys --no-osd /home/pi/bmos/videos/smack.mp4 &
# Small delay to ensure video is starting
sleep 1.8
# Do arm motion
/home/pi/bmos/servos/arms r u 1
sleep 1
/home/pi/bmos/servos/arms r d 1
