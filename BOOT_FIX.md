# Boot Configuration Fix

## Problem
After RetroPie/system updates, the boot sequence was showing:
- Raspberry Pi boot text lines (kernel messages)
- Black screen when intro video should play
- asplashscreen.service errors in logs
- Boot process not visually clean for BMO

## Root Causes

### 1. Missing Quiet Boot Parameters
The `/boot/firmware/cmdline.txt` file was missing parameters to suppress kernel messages during boot.

### 2. RetroPie Splash Screen Service Errors
The `asplashscreen.service` was trying to run VLC during early boot (sysinit.target) when the X11 environment wasn't ready yet, causing XDG_RUNTIME_DIR errors.

### 3. Redundant Splash System
BMOS already plays its own intro video via bmos.sh, making the RetroPie splash screen unnecessary.

## Solution Applied

### 1. Updated Boot Command Line (Pi5)

**File:** `/boot/firmware/cmdline.txt`

**Added Parameters:**
```
quiet splash logo.nologo vt.global_cursor_default=0
```

**What Each Does:**
- `quiet` - Suppresses most kernel log messages during boot
- `splash` - Enables the splash screen system (for Plymouth if installed)
- `logo.nologo` - Hides the Raspberry Pi rainbow logo
- `vt.global_cursor_default=0` - Hides the blinking cursor on console

**Full Command Line:**
```
console=serial0,115200 console=tty1 root=PARTUUID=fc2bddae-02 rootfstype=ext4 fsck.repair=yes rootwait cfg80211.ieee80211_regdom=GB quiet splash logo.nologo vt.global_cursor_default=0
```

**Backup Created:**
```bash
/boot/firmware/cmdline.txt.backup
```

### 2. Boot Splash Screen - Hybrid Approach

**Problem:**
Multiple attempts to use framebuffer-based splash screens (fbi) failed because X11 takes over the display when it starts, causing a gap between boot and the intro video. The splash would disappear before BMOS was ready to play its video.

**Final Solution: Desktop Wallpaper + feh Overlay**

This hybrid approach ensures moco.png is always visible during the boot-to-video transition with no black screen gaps.

**Components:**

1. **Desktop Wallpaper (Safety Layer)**
   - Set moco.png as the LXDE desktop background
   - If anything fails, you still see the BMO logo instead of blank desktop
   ```bash
   DISPLAY=:0 pcmanfm --set-wallpaper='/home/pi/RetroPie/splashscreens/moco.png' --wallpaper-mode=stretch
   ```

2. **feh Fullscreen Overlay (Primary Splash)**
   - `feh` is an X11 image viewer that launches when desktop starts
   - Shows moco.png fullscreen, covering everything
   - Stays visible until BMOS explicitly kills it

   **File:** `/etc/xdg/lxsession/LXDE-pi/autostart`
   ```bash
   @lxpanel --profile LXDE-pi
   @pcmanfm --desktop --profile LXDE-pi
   @xscreensaver -no-splash
   @feh --fullscreen --hide-pointer --auto-zoom /home/pi/RetroPie/splashscreens/moco.png
   ```

3. **BMOS Clears Splash**
   - bmos.sh kills feh right before playing intro video
   - Clean handoff from splash to video with no gap

   **File:** `/home/pi/bmos/scripts/bmos.sh` (added before video)
   ```bash
   # Kill feh splash screen before playing video
   killall feh 2>/dev/null
   ```

**Why This Works:**
- Desktop wallpaper provides fallback if timing is off
- feh fullscreen covers desktop immediately when X starts
- feh stays on top until BMOS explicitly removes it
- No gaps or black screens during transition
- No complex timing or service dependencies

**Previous Approaches That Failed:**
- Plymouth: Quits before BMOS starts, leaving gap
- fbi with systemd service: X11 takes over framebuffer, splash disappears
- fbi with PID tracking: Process exits when X11 starts
- Delayed splash clearing: Couldn't get timing right consistently

### 3. Fixed EmulationStation Launch Flow

**Problem:**
EmulationStation (RetroPie menu system) was auto-launching at boot via LXDE autostart, causing a brief flash of the RetroPie interface before BMOS appeared. This was a workaround, not the intended design.

**How It Should Work:**
1. BMOS is the main interface
2. User presses `;` (videogames button) or says "play video games"
3. BMOS plays videogames.mp4 and launches emulaunch.sh
4. BMOS closes its SDL window
5. EmulationStation opens for game browsing/launching
6. When user exits EmulationStation, emulaunch.sh restarts bmo.service
7. User returns to BMOS interface

**Solution:**
Disabled EmulationStation autostart in LXDE configuration. EmulationStation now only launches when user activates it from BMOS.

**Files Changed:**
- `~/.config/lxsession/LXDE-pi/autostart` - Removed EmulationStation autolaunch
- Removed dead reference to non-existent bmo-service.sh

**File:** `~/.config/lxsession/LXDE-pi/autostart` (after cleanup)
```bash
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
#@/home/pi/launch_emulationstation.sh  # Disabled - launches via BMOS button
```

**Integration Details:**
- BMOS code calls `run_background_command("/home/pi/bmos/scripts/emulaunch.sh -desktop")` when videogames button pressed (CDesktop.cpp:1871, 3343)
- emulaunch.sh launches EmulationStation and monitors it
- When EmulationStation exits, runs `sudo systemctl restart bmo` to return to BMOS

## Boot Sequence Now

1. **Firmware Stage:** Minimal output, no rainbow logo
2. **Kernel Boot:** Suppressed messages (quiet mode)
3. **X11 Starts:** graphical.target reached, LXDE desktop loads
4. **Desktop Wallpaper:** moco.png shows as desktop background
5. **feh Launches:** Fullscreen moco.png covers desktop (via LXDE autostart)
6. **BMOS Service Starts:** bmo.service (After=graphical.target)
7. **Splash Cleared:** bmos.sh kills feh
8. **Intro Video Plays:** mpv plays intro.mp4 for 5 seconds
9. **BMO Interface:** Faces and buttons appear

## Testing

To test the boot configuration, reboot the Pi:

```bash
ssh pi@192.168.20.186
sudo reboot
```

**Expected Behavior:**
- No kernel messages visible (or very brief)
- No Raspberry Pi logo
- BMO splash screen (moco.png) appears when X11 starts
- Splash stays visible until intro video begins (no black gaps)
- BMO intro video (intro.mp4) plays for 5 seconds
- BMO interface appears with faces
- No RetroPie/EmulationStation menu flash

**Verify After Reboot:**
```bash
# Check that feh is not running (should have been killed by bmos.sh)
ps aux | grep feh

# Verify EmulationStation is not auto-running
ps aux | grep emulationstation

# Check boot parameters
cat /boot/firmware/cmdline.txt

# Verify desktop wallpaper is set
cat ~/.config/pcmanfm/LXDE-pi/desktop-items-0.conf | grep wallpaper
```

## Rollback Instructions

If you need to restore the original configuration:

### Restore Original Boot Parameters
```bash
ssh pi@192.168.20.186
sudo cp /boot/firmware/cmdline.txt.backup /boot/firmware/cmdline.txt
sudo reboot
```

### Restore Original VLC-based Splash Script
The original script is backed up in the git repository at:
`/opt/retropie/supplementary/splashscreen/.git`

To restore it, you would need to check out the original version and re-enable it.

## Files Changed

### On Raspberry Pi
- `/boot/firmware/cmdline.txt` - Added quiet boot parameters
- `/boot/firmware/cmdline.txt.backup` - Backup of original
- `/etc/xdg/lxsession/LXDE-pi/autostart` - Added feh fullscreen splash
- `/home/pi/bmos/scripts/bmos.sh` - Added killall feh before video
- `~/.config/lxsession/LXDE-pi/autostart` - Disabled EmulationStation autostart
- `/etc/xdg/autostart/emulationstation.desktop` - Renamed to .disabled
- Desktop wallpaper set to moco.png via pcmanfm

### In Repository
- `PI5_SYNC_NOTES.md` - Updated with boot configuration section
- `BOOT_FIX.md` - This document (new)

## Related Issues Fixed

This fix addresses:
1. Seeing Pi boot text during startup
2. Black screen gaps between boot and intro video
3. BMO splash screen (moco.png) now displays consistently from X11 start until video plays
4. EmulationStation briefly appearing before BMOS (auto-launch disabled)
5. Clean boot sequence: splash screen → intro video → BMO interface (no gaps)

## Additional Changes

### Birthday Command Changed to LLM
The `~birthday==mp4:birsday.mp4` command was removed from `commands.conf`. Birthday-related questions now go directly to the LLM for dynamic responses instead of playing a pre-recorded video.

## Notes

- Changes take effect after reboot
- Boot parameters are persistent across reboots
- asplashscreen.service remains disabled until re-enabled
- BMOS intro video timing already fixed (5.5s sleep for 5.024s video)
