# Pi5 Sync Notes

## Successfully Synced from Pi5 to Repo

### Updated Files
- **bmo.txt** - Updated keyboard mappings for Pi5 configuration
- **commands.conf** - Simplified voice command list matching Pi5
- **settings.txt** - Updated intervals (FaceInterval: 10, RandomVideo: 1, RandomVideoInterval: 30)
- **scripts/bmos.sh** - Completely rewritten startup script with proper environment variables and logging

### New Files Added
- **gv/transcribe.py** - Python voice recognition using Google Speech Recognition API
- **scripts/google-voice.sh** - Wrapper script for transcribe.py
- **scripts/startbmo.sh** - Startup check script
- **scripts/choparm.sh** - Arm animation for "defend me" command
- **scripts/smackarm.sh** - Arm animation script
- **scripts/audio-init.sh** - Sets microphone gain on boot
- **scripts/rightraise.sh** - Simple right arm raise
- **scripts/game_debug.sh** - RetroP ie game launch debugger
- **config.txt** - Pi5 boot configuration
- **servos/waveright** - Right arm wave servo control script
- **servos/arms** - Main servo control binary

## Fixed Issues

### Files Created on Pi5
1. **servos/waveright** - ✅ CREATED - Now contains `/home/pi/bmos/servos/arms r w 10`
2. **faces/blank.jpeg** - ✅ CREATED - Temporary copy of bmo01.jpg (should be replaced with actual blank image)

### Files Confirmed to Exist
3. **scripts/choparm.sh** - ✅ EXISTS - Arm animation with bmochop.mp4 video
4. **scripts/smackarm.sh** - ✅ EXISTS - Arm animation with smack.mp4 video

### Cleanup Completed on Pi5
- ✅ Moved all *.log files to `/home/pi/logs/`
- ✅ Moved all debug WAV files to `/home/pi/debug_audio/`
- ✅ Organized messy home directory

### Crash Issues

#### Primary Issue: X11 Connection Crashes
- Error: `X connection to :0 broken (explicit kill or server shutdown)`
- Occurs randomly during operation
- Likely a stability/resource issue on Pi5
- May be related to SDL2 video driver configuration

#### Secondary Issues
1. **DBUS Communication Errors**
   - Error: `Must have DBUS_SESSION_BUS_ADDRESS`
   - Affects omxplayer control

2. **Network Resolution Failures** (when WiFi down)
   - Error: `[Errno -3] Temporary failure in name resolution`
   - Affects Google Speech Recognition API calls

3. **Path Issues**
   - Double slash in blank.jpeg path suggests path concatenation bug

## Voice Recognition System

### How It Works (Pi5)
1. BMOS captures audio to `/home/pi/bmos/out.wav` (32-bit stereo 48kHz)
2. BMOS calls `scripts/google-voice.sh`
3. google-voice.sh runs `gv/transcribe.py`
4. transcribe.py:
   - Converts audio to 16-bit mono 16kHz
   - Sends to Google Speech Recognition API (en-AU)
   - Checks result against commands.conf patterns
   - Returns matching command text or "what" if no match
5. BMOS parses returned text and executes command

### Command Matching Logic
- **Exact match**: Command without `~` prefix must match exactly (case-insensitive)
- **Fuzzy match**: Command with `~` prefix matches if found anywhere in recognized text
- If no match found, returns default "what" response

## Recommendations

### Immediate Actions Needed
1. Create missing servo executables or update commands.conf to use existing ones
2. Fix blank.jpeg path issue (remove double slash)
3. Verify choparm.sh and smackarm.sh exist, or remove references
4. Test X11 stability - may need to adjust SDL2 configuration

### Future Enhancements
1. **LLM Integration** - Replace text-based command matching with LLM for natural language understanding
2. **Error Handling** - Better graceful degradation when network unavailable
3. **Cleanup** - Remove debug files and logs from Pi home directory
4. **Documentation** - Add setup instructions for Pi5-specific configuration

## Dependencies (Pi5)
- Python 3 with speech_recognition library
- Google Speech Recognition API (requires internet)
- SDL2 (video/graphics)
- ALSA (audio)
- omxplayer (video playback)
- PCA9685 driver (servo control)
