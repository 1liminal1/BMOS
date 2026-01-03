#!/bin/bash

if ! pidof -x bmos > /dev/null
then
    /home/pi/bmos/scripts/bmos.sh
fi
