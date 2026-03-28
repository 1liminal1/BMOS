# BMO Fallback Systems

This document describes the fallback mechanisms implemented for BMO to ensure reliable operation even when primary services are unavailable.

## WiFi Fallback System

### Overview
BMO automatically tries multiple WiFi networks in priority order to maintain internet connectivity.

### Network Priority
1. **IoT** (Primary) - Home WiFi network
2. **iPhone** (First Fallback) - Mobile hotspot for portable operation
3. **IQ** (Second Fallback) - Alternative network

### How It Works

**Script:** `/home/pi/bmos/scripts/wifi-fallback.sh`
- Checks current internet connectivity by pinging 8.8.8.8
- If no connectivity, tries each network in priority order
- Logs all connection attempts to `/home/pi/wifi-fallback.log`

**Service:** `wifi-fallback.service`
- Runs the fallback script once at boot (after network-online.target)
- Can be manually triggered: `sudo systemctl start wifi-fallback.service`

**Timer:** `wifi-fallback.timer`
- Automatically runs fallback check every 5 minutes
- First check runs 1 minute after boot
- Ensures BMO reconnects if WiFi drops

### Usage

**Check WiFi Status:**
```bash
nmcli device wifi
```

**View Fallback Logs:**
```bash
tail -f /home/pi/wifi-fallback.log
```

**Manually Trigger Fallback:**
```bash
sudo systemctl start wifi-fallback.service
```

**Check Timer Status:**
```bash
systemctl status wifi-fallback.timer
```

### Adding New WiFi Networks

To add a new fallback network:

1. Connect to the network manually first:
```bash
nmcli device wifi connect "SSID" password "PASSWORD"
```

2. Edit the fallback script:
```bash
sudo nano /home/pi/bmos/scripts/wifi-fallback.sh
```

3. Add the network SSID to the `NETWORKS` array in priority order:
```bash
NETWORKS=("IoT" "iPhone" "IQ" "NewNetwork")
```

## Home Assistant Fallback System

### Overview
BMO voice assistant tries multiple Home Assistant URLs to maintain voice functionality when the primary server is unavailable.

### HA URL Priority
1. **https://YOUR_HA_DOMAIN** (Primary) - Local Home Assistant instance
2. **https://YOUR_NABU_CASA_URL.ui.nabu.casa** (Fallback) - Nabu Casa remote access

### How It Works

**Script:** `/home/pi/bmos/ha/ha_assist.py`

The script automatically:
1. Tries each HA URL in order when processing voice commands
2. Tests connectivity to `/api/` endpoint with authentication
3. Uses the first working URL for the voice pipeline
4. Logs which URL is being used

### Voice Pipeline with Fallback

When BMO receives a voice command:
1. Checks if primary HA (YOUR_HA_DOMAIN) is reachable
2. If primary fails, tries Nabu Casa remote URL
3. Sends audio to working HA for:
   - Speech-to-text (Whisper)
   - LLM conversation (OpenAI)
   - Text-to-speech (Piper)
4. Returns response audio to BMO

### Logs

**Location:** `/home/pi/bmos/bmos_error.log`

**Example Log Output:**
```
[16:40:20] HA-Voice: Checking HA at https://YOUR_HA_DOMAIN/api/
[16:40:20] HA-Voice: HA available at https://YOUR_HA_DOMAIN
[16:40:20] HA-Voice: Sending to Assist Pipeline API
```

or if fallback is used:

```
[16:40:20] HA-Voice: Checking HA at https://YOUR_HA_DOMAIN/api/
[16:40:20] HA-Voice: HA check failed for https://YOUR_HA_DOMAIN: Connection timeout
[16:40:23] HA-Voice: Checking HA at https://YOUR_NABU_CASA_URL.ui.nabu.casa/api/
[16:40:23] HA-Voice: HA available at https://YOUR_NABU_CASA_URL.ui.nabu.casa
```

### Adding New HA URLs

To add additional Home Assistant fallback URLs:

1. Edit the HA script:
```bash
nano /home/pi/bmos/ha/ha_assist.py
```

2. Add URLs to the `HA_URLS` list in priority order:
```python
HA_URLS = [
    "https://YOUR_HA_DOMAIN",  # Primary
    "https://YOUR_NABU_CASA_URL.ui.nabu.casa",  # Nabu Casa
    "https://new-ha-url.com"  # Additional fallback
]
```

3. Restart BMO to apply changes:
```bash
sudo systemctl restart bmo
```

## Testing Fallback Systems

### Test WiFi Fallback

1. Disconnect from current WiFi:
```bash
nmcli connection down "IoT"
```

2. Watch the fallback happen:
```bash
tail -f /home/pi/wifi-fallback.log
```

3. Verify connection to fallback network:
```bash
nmcli device wifi
```

### Test HA Fallback

1. Temporarily block primary HA (edit /etc/hosts):
```bash
echo "127.0.0.1 YOUR_HA_DOMAIN" | sudo tee -a /etc/hosts
```

2. Try voice command in BMO

3. Check logs to verify Nabu Casa was used:
```bash
tail /home/pi/bmos/bmos_error.log
```

4. Restore access:
```bash
sudo sed -i '/127.0.0.1 YOUR_HA_DOMAIN/d' /etc/hosts
```

## Files Changed

### WiFi Fallback
- `/home/pi/bmos/scripts/wifi-fallback.sh` - Fallback script (new)
- `/etc/systemd/system/wifi-fallback.service` - Service definition (new)
- `/etc/systemd/system/wifi-fallback.timer` - Timer for periodic checks (new)
- `/home/pi/wifi-fallback.log` - Log file (created automatically)

### Home Assistant Fallback
- `/home/pi/bmos/ha/ha_assist.py` - Updated with URL fallback logic
- `/home/pi/bmos/ha/ha_assist.py.backup` - Backup of original (created automatically)
- `/home/pi/bmos/bmos_error.log` - Existing log file used for HA messages

## Troubleshooting

### WiFi Fallback Not Working

**Check timer is running:**
```bash
systemctl status wifi-fallback.timer
```

**Check service logs:**
```bash
journalctl -u wifi-fallback.service
```

**Manually test script:**
```bash
/home/pi/bmos/scripts/wifi-fallback.sh
cat /home/pi/wifi-fallback.log
```

### HA Fallback Not Working

**Check HA URLs are reachable:**
```bash
curl -I https://YOUR_HA_DOMAIN/api/
curl -I https://YOUR_NABU_CASA_URL.ui.nabu.casa/api/
```

**Check HA token is valid:**
- Token expires in 2082 (year)
- If expired, generate new long-lived token in HA

**View detailed logs:**
```bash
tail -100 /home/pi/bmos/bmos_error.log | grep HA-Voice
```

## Benefits

### Reliability
- BMO continues working when primary WiFi drops
- Voice assistant works remotely via Nabu Casa
- Automatic recovery without user intervention

### Portability
- BMO can connect to phone hotspot for demos
- Works at different locations with configured networks
- Remote access via Nabu Casa when away from home

### Monitoring
- All fallback events logged for debugging
- Timer ensures periodic connectivity checks
- Easy to verify which systems are in use
