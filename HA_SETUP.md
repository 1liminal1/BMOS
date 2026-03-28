# BMOS Home Assistant LLM Integration Setup

## Overview
This setup adds LLM-powered voice responses to BMOS with talking face animation. When you press the record button, BMO will:
1. Record your voice
2. Send to Home Assistant for Whisper transcription
3. Get intelligent response from OpenAI
4. Play TTS audio while moving face and arms
5. Falls back to Google Speech Recognition if HA unavailable

## Features Added
- **Talking Face Animation**: BMO's face cycles through bmo04.jpg, bmo05.jpg, bmo07.jpg at 120ms intervals while speaking
- **Action Commands**: LLM can trigger arm movements during speech using [ACTION:xxx] tags
- **HA Integration**: Direct REST API calls to Home Assistant
- **Google Fallback**: If HA is unavailable, falls back to existing Google Speech Recognition

## Prerequisites
1. Home Assistant running and accessible from Pi
2. OpenAI integration configured in Home Assistant
3. Whisper STT configured in Home Assistant
4. Piper TTS (or other TTS) configured in Home Assistant
5. Python 3 with requests library on Pi

## Setup Steps

### 1. Install Python Dependencies on Pi
```bash
ssh pi@YOUR_PI_IP
sudo apt-get install python3-requests
```

### 2. Create Home Assistant Long-Lived Access Token
1. In Home Assistant, go to your profile (bottom left)
2. Scroll down to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Name it "BMOS Integration"
5. Copy the token (you won't see it again!)

### 3. Configure ha_assist.py
Edit `/home/pi/bmos/ha/ha_assist.py` and update these lines:

```python
HA_URL = "http://YOUR_HA_IP:8123"  # Replace with your HA URL (e.g., http://192.168.1.100:8123)
HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"  # Paste your token here
CONVERSATION_AGENT = "conversation.openai"  # Your OpenAI conversation agent ID
```

To find your conversation agent ID:
```bash
curl -X GET -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_HA_IP:8123/api/conversation/agent/list
```

### 4. Configure OpenAI Conversation Agent in Home Assistant

Your OpenAI conversation agent needs to be configured to use action tags. In your Home Assistant configuration.yaml or via UI:

**System Prompt Example:**
```
You are BMO from Adventure Time. You are helpful, playful, and enthusiastic.
Keep responses short (1-2 sentences).

You can perform actions by including tags in your response:
- [ACTION:wave_arms] - Wave both arms
- [ACTION:wave_right] - Wave right arm
- [ACTION:wave_left] - Wave left arm
- [ACTION:defend] - Defensive arm position

Example responses:
"Hello friend! [ACTION:wave_arms]"
"I'll protect you! [ACTION:defend]"
"Watch this! [ACTION:wave_right]"

Only use action tags when appropriate to the conversation.
```

### 5. Copy Files to Pi
From your Windows machine:
```bash
# SSH to Pi
ssh pi@YOUR_PI_IP

# Backup current BMOS binary
cd /home/pi/bmos
cp bmos bmos.backup

# Exit Pi, then from Windows copy updated files
```

Use WinSCP or similar to copy these files to Pi:
- `CDesktop.cpp` → `/home/pi/bmos/CDesktop.cpp`
- `CDesktop.h` → `/home/pi/bmos/CDesktop.h`
- `ha/ha_assist.py` → `/home/pi/bmos/ha/ha_assist.py`
- `scripts/ha-voice.sh` → `/home/pi/bmos/scripts/ha-voice.sh`

Or via PowerShell/SCP:
```powershell
scp ./CDesktop.cpp pi@YOUR_PI_IP:/home/pi/bmos/
scp ./CDesktop.h pi@YOUR_PI_IP:/home/pi/bmos/
scp ./ha\ha_assist.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
scp ./scripts\ha-voice.sh pi@YOUR_PI_IP:/home/pi/bmos/scripts/
```

### 6. Make Scripts Executable
```bash
ssh pi@YOUR_PI_IP
chmod +x /home/pi/bmos/ha/ha_assist.py
chmod +x /home/pi/bmos/scripts/ha-voice.sh
```

### 7. Rebuild BMOS on Pi
```bash
ssh pi@YOUR_PI_IP
cd /home/pi/bmos
make clean
make
```

### 8. Test HA Integration
Before running BMOS, test the HA integration:

```bash
# Record test audio (or use existing last.wav)
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/last.wav

# Test HA integration
python3 /home/pi/bmos/ha/ha_assist.py

# Should output something like:
# tts:/home/pi/bmos/tts_response.wav|action:wave_arms
```

If it fails, check:
- HA URL is correct and accessible from Pi
- Token is valid
- Whisper, OpenAI, and TTS are configured in HA

### 9. Start BMOS
```bash
cd /home/pi/bmos
./bmos
```

### 10. Test Voice Commands
1. Press the record button (or say "BMO" if wake word enabled)
2. Say something like "Hello BMO, wave at me"
3. BMO should:
   - Transcribe via Whisper
   - Get LLM response from OpenAI
   - Play TTS audio
   - Show talking face animation (bmo04, 05, 07 cycling)
   - Wave arms if [ACTION:wave_arms] in response

## Troubleshooting

### HA Integration Not Working
Check logs:
```bash
tail -f /home/pi/game_logs/bmos_*.log
```

Test HA connection manually:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}' \
  http://YOUR_HA_IP:8123/api/conversation/process
```

### Falls Back to Google Every Time
- Verify HA_URL and HA_TOKEN in ha_assist.py
- Check Pi can reach HA: `ping YOUR_HA_IP`
- Verify HA services are running

### No Talking Face Animation
- Check face files exist: `ls /home/pi/bmos/faces/bmo0*.jpg`
- Should have bmo04.jpg, bmo05.jpg, bmo07.jpg
- Check BMOS console output for errors

### Arms Not Moving
- Verify action is in response: check stderr output from ha_assist.py
- Test servo commands manually:
  ```bash
  /home/pi/bmos/servos/waveboth
  /home/pi/bmos/scripts/rightraise.sh
  ```

### TTS Audio Not Playing
- Check TTS file created: `ls -l /home/pi/bmos/tts_response.wav`
- Test audio playback: `aplay /home/pi/bmos/tts_response.wav`
- Verify audio output device configured

## Available Actions
These actions can be triggered by including tags in LLM responses:

- `[ACTION:wave_arms]` - Wave both arms (calls `/home/pi/bmos/servos/waveboth`)
- `[ACTION:wave_right]` - Wave right arm (calls `/home/pi/bmos/servos/waveright`)
- `[ACTION:wave_left]` - Wave left arm (calls `/home/pi/bmos/servos/waveleft`)
- `[ACTION:defend]` - Defensive position (calls `/home/pi/bmos/scripts/choparm.sh`)

Actions execute at the START of TTS playback, so arms move while speaking.

## Code Changes Summary

### CDesktop.h
- Added `bool mTalking`, `Uint32 mTalkingTimer`, `int mTalkingFace`
- Added `void PlayTTS(char* audiofile, char* action)`

### CDesktop.cpp
**Line 1439**: Fixed zombie process bug - moved `CheckPid()` outside conditional

**Lines 1445-1454**: Added talking face animation loop
```cpp
if (mTalking && SDL_TICKS_PASSED_FIXED(ticks, mTalkingTimer))
{
    const char* talkingFaces[] = {"bmo04.jpg", "bmo05.jpg", "bmo07.jpg"};
    SetFace(talkingFaces[mTalkingFace]);
    mTalkingFace = (mTalkingFace + 1) % 3;
    mTalkingTimer = ticks + 120;
}
```

**Lines 2859-2916**: New `PlayTTS()` function that:
- Starts talking face animation
- Executes action command (arm movement)
- Plays TTS audio with aplay
- Stops animation and resets to bmo01.jpg

**Lines 3124-3187**: Modified voice processing to:
- Use `ha-voice.sh` instead of `google-voice.sh`
- Detect `tts:` responses
- Parse format `tts:/path|action:xxx`
- Call `PlayTTS()` with audio file and action

### New Files
- `ha/ha_assist.py` - HA integration script
- `scripts/ha-voice.sh` - Wrapper with Google fallback

## Fallback Behavior
If HA integration fails (network issue, HA down, etc.):
1. ha_assist.py exits with code 1
2. ha-voice.sh detects failure
3. Automatically runs google-voice.sh (existing system)
4. Regular command matching continues to work

This ensures BMO always works even if HA is unavailable.

## Next Steps / Future Enhancements
- Add more action commands (dance, sing, etc.)
- Support multiple TTS voices
- Add conversation history/context
- Wake word detection integration
- Voice activity detection for hands-free mode
