#!/bin/bash
# WiFi Fallback Script - Try networks in priority order
# Priority: IoT -> iPhone -> IQ

LOG="/home/pi/wifi-fallback.log"
exec 1>>"$LOG" 2>&1

echo "=== WiFi Fallback Check $(date) ==="

# Check if we have internet connectivity
check_connectivity() {
    ping -c 2 -W 3 8.8.8.8 >/dev/null 2>&1
    return $?
}

# Get current SSID
get_current_ssid() {
    nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d':' -f2
}

CURRENT_SSID=$(get_current_ssid)
echo "Current SSID: $CURRENT_SSID"

# Check if we have connectivity
if check_connectivity; then
    echo "Internet connected on $CURRENT_SSID - no action needed"
    exit 0
fi

echo "No internet connectivity - trying fallback networks..."

# Network priority list
NETWORKS=("IoT" "iPhone" "IQ")

for NETWORK in "${NETWORKS[@]}"; do
    echo "Trying to connect to: $NETWORK"
    
    # Try to connect to this network
    nmcli connection up "$NETWORK" >/dev/null 2>&1
    
    # Wait a moment for connection to establish
    sleep 5
    
    # Check if we now have connectivity
    if check_connectivity; then
        echo "Successfully connected to $NETWORK"
        exit 0
    else
        echo "Failed to get connectivity on $NETWORK"
    fi
done

echo "Failed to connect to any network"
exit 1
