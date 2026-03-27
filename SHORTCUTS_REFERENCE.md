# BMOS Shortcuts & Commands Reference

Complete reference for keyboard shortcuts, controller hotkeys, voice commands, and system operations.

## EmulationStation / RetroPie

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **F4** | Exit EmulationStation (returns to BMOS) |
| **F1** | Open EmulationStation menu |
| **Ctrl+F4** | Shut down the system |
| **Arrow Keys** | Navigate menus |
| **Enter** | Select/Confirm |
| **Backspace** | Back/Cancel |

### Controller Hotkeys (RetroArch - In Game)

**Standard hotkey combination: Hold Select + Button**

| Combination | Action |
|-------------|--------|
| **Select + Start** | Exit game (return to EmulationStation) |
| **Select + Right Shoulder** | Save state |
| **Select + Left Shoulder** | Load state |
| **Select + Right** | Next save state slot |
| **Select + Left** | Previous save state slot |
| **Select + Up** | Increase volume |
| **Select + Down** | Decrease volume |
| **Select + X** | RetroArch menu |
| **Select + B** | Reset game |
| **Select + Y** | Toggle menu |

**Note:** Select button must be configured as the "Hotkey Enable" button in RetroArch for these to work.

### Controller Configuration

- **Initial Setup**: When EmulationStation first starts, hold any button on controller to begin configuration
- **Reconfigure Controller**:
  - Navigate to RetroPie menu in EmulationStation
  - Select "Configuration"
  - Or via SSH: `rm /opt/retropie/configs/all/emulationstation/es_input.cfg`

## BMOS Interface

### Button Controls

| Button | Action |
|--------|--------|
| **;** (semicolon) | Launch video games (EmulationStation) |
| **Voice button** | Activate voice recognition |

### Voice Commands

#### Built-in Commands (No LLM)

| Command | Action |
|---------|--------|
| "say hi to" / "hello" | Play hello video |
| "photos" | Launch photos app |
| "emotes" | Launch BMO emotes |
| "about box" | Show about information |
| "play video games" / "video games" | Launch EmulationStation |
| "how many fingers am i holding up" / "beep" / "beat" / "beef" | Play beep video |
| "you're funny" / "make me laugh" | Play laugh video |
| "wave your arms" | Wave both arms |
| "wave your arm" | Wave right arm |
| "defend me" | Execute chop arm script |

#### LLM Commands

Any voice command not matching the above will be sent to Home Assistant LLM for processing, including:
- General questions
- Smart home control
- Conversational responses
- Birthday wishes (now uses LLM instead of video)

### Configuration Files

- **Voice Commands**: `/home/pi/bmos/commands.conf`
- **Add new command**: Edit commands.conf with format: `command==action:parameter`

## System Operations

### SSH Access

```bash
ssh pi@192.168.20.186
```

### Service Management

```bash
# Restart BMOS
sudo systemctl restart bmo

# Check BMOS status
sudo systemctl status bmo

# View BMOS logs
journalctl -u bmo.service -f

# View startup logs
tail -f /home/pi/bmos_startup.log
```

### WiFi Management

```bash
# Check current connection
nmcli device wifi

# List saved networks
nmcli connection show

# Connect to network
nmcli connection up "NetworkName"

# WiFi fallback logs
tail -f /home/pi/wifi-fallback.log
```

### Bluetooth Controller

```bash
# Check controller connection
bluetoothctl info E4:17:D8:58:D1:32

# Reconnect controller
bluetoothctl connect E4:17:D8:58:D1:32

# List paired devices
bluetoothctl devices
```

### Display & Screensaver

```bash
# Disable screensaver (current session)
DISPLAY=:0 xset s off
DISPLAY=:0 xset -dpms
DISPLAY=:0 xset s noblank

# Check screensaver status
DISPLAY=:0 xset q | grep "Screen Saver"
```

### Video Playback

BMOS uses **mpv** for video playback on Pi 5:
- Intro video: `/home/pi/bmos/videos/intro.mp4`
- Video player configured in: `CDesktop.cpp`
- Startup script: `/home/pi/bmos/scripts/bmos.sh`

### File Transfer

**Network Transfer to Pi:**
```
\\192.168.20.186\roms      # ROM files
\\192.168.20.186\bios      # BIOS files
\\192.168.20.186\configs   # Config files
```

**SCP from Windows:**
```bash
scp file.ext pi@192.168.20.186:/home/pi/destination/
```

## Development & Debugging

### Logs

| Log File | Purpose |
|----------|---------|
| `/home/pi/bmos_startup.log` | BMOS startup script output |
| `/home/pi/bmos_error.log` | Home Assistant voice integration |
| `/home/pi/wifi-fallback.log` | WiFi fallback events |
| `/home/pi/splash_boot.log` | Boot splash screen (legacy) |
| `/opt/retropie/configs/all/emulationstation/es_log.txt` | EmulationStation logs |

### Quick Diagnostics

```bash
# Check if BMOS is running
ps aux | grep bmos

# Check if EmulationStation is running
ps aux | grep emulationstation

# Check display
echo $DISPLAY

# Test video playback
mpv --fs /home/pi/bmos/videos/intro.mp4

# Test Home Assistant connection
python3 /home/pi/bmos/ha/ha_assist.py
```

### Recompile BMOS

```bash
cd /home/pi/bmos
make clean
make
sudo systemctl restart bmo
```

## Hardware Control

### Servo Arms

Scripts located in `/home/pi/bmos/scripts/`:
- `armsinit.sh` - Initialize servos
- `armsdown.sh` - Move arms down
- `waveboth` - Wave both arms
- `waveright` - Wave right arm
- `choparm.sh` - Chop motion
- `smackarm.sh` - Smack motion
- `fistbump.sh` - Fist bump motion

**Manual servo control:**
```bash
/home/pi/bmos/scripts/waveboth
```

## Troubleshooting Shortcuts

### Quick Fixes

**BMOS not responding:**
```bash
sudo systemctl restart bmo
```

**EmulationStation stuck:**
```bash
killall emulationstation
```

**Controller not working:**
```bash
# Check Bluetooth
bluetoothctl info E4:17:D8:58:D1:32

# Reconnect
bluetoothctl connect E4:17:D8:58:D1:32
```

**Screen asleep:**
```bash
DISPLAY=:0 xset dpms force on
DISPLAY=:0 xset s reset
```

**WiFi not working:**
```bash
# Manually trigger fallback
sudo systemctl start wifi-fallback.service

# Check logs
tail /home/pi/wifi-fallback.log
```

**Home Assistant not responding:**
```bash
# Check HA voice logs
tail /home/pi/bmos_error.log | grep HA-Voice
```

## Emergency Access

### If BMOS is completely broken

1. **SSH in and stop BMOS:**
   ```bash
   ssh pi@192.168.20.186
   sudo systemctl stop bmo
   ```

2. **Access desktop directly:**
   - Connect monitor and keyboard
   - System will show LXDE desktop
   - Open terminal to fix issues

3. **Restore from backup:**
   ```bash
   cd /home/pi/bmos
   git checkout main
   sudo systemctl restart bmo
   ```

### Safe Mode Boot

No official safe mode, but you can disable BMOS auto-start:
```bash
sudo systemctl disable bmo
sudo reboot
```

To re-enable:
```bash
sudo systemctl enable bmo
```

## Configuration Locations

### BMOS Files
- Main binary: `/home/pi/bmos/bmos`
- Scripts: `/home/pi/bmos/scripts/`
- Videos: `/home/pi/bmos/videos/`
- Commands: `/home/pi/bmos/commands.conf`
- HA integration: `/home/pi/bmos/ha/ha_assist.py`

### System Files
- Service: `/etc/systemd/system/bmo.service`
- LXDE autostart: `/etc/xdg/lxsession/LXDE-pi/autostart`
- Boot splash: Desktop wallpaper + feh overlay
- WiFi fallback: `/home/pi/bmos/scripts/wifi-fallback.sh`

### RetroPie Files
- ROMs: `/home/pi/RetroPie/roms/`
- BIOS: `/home/pi/RetroPie/BIOS/`
- Configs: `/opt/retropie/configs/`
- EmulationStation config: `/opt/retropie/configs/all/emulationstation/`

## Quick Reference Card

**Most Used Commands:**

| What | How |
|------|-----|
| Exit game | Select + Start |
| Exit EmulationStation | F4 key |
| Restart BMOS | `sudo systemctl restart bmo` |
| Kill EmulationStation | `killall emulationstation` |
| Check controller | `bluetoothctl info E4:17:D8:58:D1:32` |
| WiFi fallback log | `tail /home/pi/wifi-fallback.log` |
| BMOS startup log | `tail /home/pi/bmos_startup.log` |
| Voice assistant log | `tail /home/pi/bmos_error.log` |

## Documentation Files

For more detailed information, see:
- `README.md` - Overview and setup
- `PI5_SYNC_NOTES.md` - Pi 5 migration notes
- `BOOT_FIX.md` - Boot sequence configuration
- `FALLBACK_SYSTEMS.md` - WiFi and HA fallback systems
- `HA_SETUP.md` - Home Assistant integration
- `TESTING_GUIDE.md` - Testing procedures
- `DEPLOY_VIDEO_PRIORITY.md` - Video deployment guide
