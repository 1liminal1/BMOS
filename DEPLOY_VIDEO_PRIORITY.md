# Deploy Video Command Priority + Action Mapping

## Overview
This update adds two major features:
1. **Video Command Priority**: Prevents video commands from triggering both video playback AND LLM TTS responses
2. **Action Mapping**: Automatically adds actions (wave_arms, wave_right, etc.) based on what the LLM SAYS in its response

When a voice command matches a video/system command in commands.conf, it will ONLY execute that command and skip the LLM. When the LLM's response contains words like "hello", "yay", or "goodbye", actions are automatically added WITHOUT needing [ACTION:xxx] tags in the HA prompt.

## Changes Made

### New Files
1. **ha/command_matcher.py** - Parses commands.conf and checks if transcribed text matches a video/system command, plus action mapping
2. **ha/test_matcher.py** - Test script to verify command matching and action mapping work correctly

### Modified Files
1. **ha/ha_assist_ws.py** - Now checks for video commands AND suggests actions based on transcription

## Files to Copy to Pi

Copy these files from Windows to Pi:

```powershell
# From PowerShell on Windows:
scp ./ha\command_matcher.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
scp ./ha\test_matcher.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
scp ./ha\ha_assist_ws.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
```

## Testing Steps

### 1. Test Command Matcher (Optional)
```bash
ssh pi@YOUR_PI_IP
cd /home/pi/bmos/ha
python3 test_matcher.py
```

Expected output:
- "defend me" → Should match system command
- "wave your arms" → Should match system command
- "hello" → Should match mp4 video
- "what time is it" → No match (LLM handles)

### 2. Test with Real Voice Commands

#### Test Video Command (should NOT trigger LLM):
```bash
# Record saying "defend me"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py

# Expected output:
# "defend me"
# (NOT "tts:/home/pi/bmos/tts_response.wav")
```

#### Test Non-Video Command (should trigger LLM):
```bash
# Record saying "what time is it"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py

# Expected output:
# "tts:/home/pi/bmos/tts_response.wav"
```

### 3. Check Logs
```bash
tail -f /home/pi/bmos/bmos_error.log
```

Look for lines like:
- `Video command matched: mp4:hello.mp4` - Video command detected
- `Video command takes priority, skipping TTS` - LLM was skipped
- `Pipeline processing complete` - LLM response generated

## How It Works

### Flow Diagram
```
Voice Input → Whisper STT → Transcription
                                    ↓
                    Check commands.conf + action patterns
                                    ↓
                    ┌───────────────┴────────────────┐
                    ↓                                ↓
            Video Command Match?              No Match?
                    ↓                                ↓
         Output: "defend me"        OpenAI LLM → TTS Response
         BMOS plays video                     ↓
         (may have action)          Check for action:
                                    - LLM [ACTION:xxx] tag?
                                    - OR pattern match (yay, hi, etc.)?
                                              ↓
                                    Output: "tts:path|action:wave_arms"
```

### Detailed Steps

1. User says voice command
2. Audio sent to HA WebSocket Pipeline
3. Whisper transcribes audio → e.g., "yay bmo!"
4. **NEW**: Check transcription for:
   - Video/system command in commands.conf?
   - Action pattern match (yay, hi, defend, etc.)?

5. **If video command matched** (e.g., "defend me"):
   - Output transcribed text only: `"defend me"`
   - BMOS processes via commands.conf → plays video/runs script
   - Action may be suggested but handled by commands.conf
   - Skip LLM entirely

6. **If no video command matched** (e.g., "good morning"):
   - Send to OpenAI conversation agent
   - Get TTS response (e.g., "Hello friend!")
   - Check LLM response for action patterns:
     - LLM response tag: `[ACTION:wave_arms]` (takes priority)
     - OR response text pattern: "Hello" → `wave_right`
   - Output: `"tts:/home/pi/bmos/tts_response.wav|action:wave_right"`

## Video Commands in commands.conf

These commands will now skip LLM and go directly to video/system:

**Exact Matches:**
- `hello` → mp4:hello.mp4
- `defend me` → system:/home/pi/bmos/scripts/choparm.sh
- `are you ready` → mp4:areyouready.mp4
- (etc.)

**Partial Matches (prefix ~):**
- `~wave your arms` → Matches "wave your arms", "please wave your arms", etc.
- `~you're funny` → Matches "you're funny", "that's funny", etc.
- (etc.)

## Rollback Instructions

If this causes issues, revert to previous version:

```bash
ssh pi@YOUR_PI_IP
cd /home/pi/bmos/ha

# Restore original ha_assist_ws.py from backup
# (Make backup first before deploying!)
cp ha_assist_ws.py ha_assist_ws.py.video_priority
# Then restore from git or previous backup
```

## Action Patterns

The command matcher automatically detects actions based on the **LLM's response text** (not the user's input):

| Pattern in LLM Response | Action | Example LLM Responses |
|---------|--------|----------------|
| yay, hooray, woohoo, celebrate | `wave_arms` | "Yay! That's great!", "Hooray!", "Woohoo!" |
| hi, hello, hey, greetings | `wave_right` | "Hello friend!", "Hi there!", "Hey!" |
| goodbye, bye, see you | `wave_left` | "Goodbye!", "Bye!", "See you later!" |
| defend, protect, guard | `defend` | "I'll defend you!", "Let me protect that!" |

**How It Works:**
- User says: "Good morning BMO"
- LLM responds: "Hello friend! How are you?"
- Pattern matches: "Hello" → `wave_right`
- Output: `"tts:/home/pi/bmos/tts_response.wav|action:wave_right"`
- Result: BMO speaks AND waves right arm

**Priority:**
- LLM `[ACTION:xxx]` tags take priority (if you still want to use them)
- If no LLM action tag, response text pattern is checked
- If neither, no action is added to output

**HA Prompt Simplification:**
You can now REMOVE all `[ACTION:xxx]` instructions from your HA conversation prompt! The action mapping happens automatically based on what BMO naturally says.

## Next Steps After Deploy

### Test Video Commands (should skip LLM)
1. Say "defend me" - should play choparm.sh script only, no TTS
2. Say "wave your arms" - should execute waveboth only, no TTS
3. Say "hello" - should play hello.mp4 AND wave right arm, no TTS

### Test Action Mapping (should use LLM + automatic action from response)
4. Say "good morning" - if LLM says "Hello", should wave_right
5. Say "great job" - if LLM says "Yay" or "Hooray", should wave_arms
6. Say "I'm leaving" - if LLM says "Goodbye" or "Bye", should wave_left

### Test Regular LLM (no video, no action)
7. Say "what time is it" - should get LLM TTS response, no action
8. Say "tell me a joke" - should get LLM TTS response, no action

### Verify
9. No more simultaneous video + TTS playback
10. Actions work for both video commands AND LLM responses
11. Check logs to see which actions come from LLM vs matcher
