#!/bin/bash

# Wait for sound system to be ready
sleep 2

# Set microphone gain to maximum
amixer -c 1 cset numid=1 255

# Log the settings for debugging
logger "BMO audio initialization complete"
amixer -c 1 cget numid=1 | logger
