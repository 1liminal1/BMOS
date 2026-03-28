# BMOS Voice + Action Testing Guide

## Part 1: Deploy Files to Pi

```powershell
# From Windows PowerShell:
scp ./ha\command_matcher.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
scp ./ha\test_matcher.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
scp ./ha\ha_assist_ws.py pi@YOUR_PI_IP:/home/pi/bmos/ha/
```

## Part 2: Test Command Matcher (Optional)

```bash
ssh pi@YOUR_PI_IP
cd /home/pi/bmos/ha
python3 test_matcher.py
```

Expected: All tests should PASS (24 passed, 0 failed)

---

## Part 3: Find Correct Video Volume

The video volume is hardcoded in 3 places in CDesktop.cpp using mpv's `--volume` parameter:
- PlayVideo() - uses `--volume=50`
- PlayVideoSync() - uses `--volume=50`
- PlayVideoUSB() - uses `--volume=50`

Current value: **50** (50% volume, range 0-100)

### Test Different Volume Levels

```bash
ssh pi@YOUR_PI_IP

# First, play a TTS file to hear reference volume
aplay /home/pi/bmos/tts_response.wav

# Now test different video volumes using mpv
```

### Quick Volume Test Method

Test mpv volume manually:

```bash
# Test current volume (50%)
mpv --fs --volume=50 --quiet /home/pi/bmos/videos/hello.mp4

# Test quieter volumes
mpv --fs --volume=40 --quiet /home/pi/bmos/videos/hello.mp4
mpv --fs --volume=30 --quiet /home/pi/bmos/videos/hello.mp4
mpv --fs --volume=20 --quiet /home/pi/bmos/videos/hello.mp4

# Test louder volumes (if needed)
mpv --fs --volume=60 --quiet /home/pi/bmos/videos/hello.mp4
mpv --fs --volume=70 --quiet /home/pi/bmos/videos/hello.mp4
```

**When you find the right volume**, note the value and update CDesktop.cpp with it.

Common values:
- `70` = louder
- `60` = moderately louder
- `50` = current setting (50%)
- `40` = moderately quieter
- `30` = quieter
- `20` = very quiet

---

## Part 4: Test Voice Integration End-to-End

### Setup

1. Make sure HA conversation prompt is updated (see below)
2. Deploy files (Part 1)
3. Optionally run test_matcher.py (Part 2)

### Test 1: Video Command (Should Skip LLM)

```bash
# Record saying "defend me"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py
```

**Expected Output:**
```
"defend me"
```

**Expected Log Messages:**
```
[HH:MM:SS] HA-Pipeline: Transcribed: defend me
[HH:MM:SS] HA-Pipeline: Video command matched in commands.conf
[HH:MM:SS] HA-Pipeline: Video command takes priority, skipping TTS
```

**Expected Behavior:**
- NO LLM call
- NO TTS generation
- BMOS will run `/home/pi/bmos/scripts/choparm.sh` when it processes the response

---

### Test 2: Greeting (Should Use LLM + Wave Right)

```bash
# Record saying "good morning BMO"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py
```

**Expected Output:** (if LLM says "Hello")
```
"tts:/home/pi/bmos/tts_response.wav|action:wave_right"
```

**Expected Log Messages:**
```
[HH:MM:SS] HA-Pipeline: Transcribed: good morning bmo
[HH:MM:SS] HA-Pipeline: LLM Response: Hello friend! BMO is ready to play!
[HH:MM:SS] HA-Pipeline: Action: wave_right (from response pattern)
[HH:MM:SS] HA-Pipeline: Pipeline processing complete
```

**Expected Behavior:**
- LLM called
- TTS file created
- BMO speaks "Hello friend! BMO is ready to play!"
- BMO waves right arm (because response contains "Hello")

---

### Test 3: Excitement (Should Use LLM + Wave Both Arms)

```bash
# Record saying "we did it BMO!"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py
```

**Expected Output:** (if LLM says "Yay" or "Hooray")
```
"tts:/home/pi/bmos/tts_response.wav|action:wave_arms"
```

**Expected Log Messages:**
```
[HH:MM:SS] HA-Pipeline: Transcribed: we did it bmo
[HH:MM:SS] HA-Pipeline: LLM Response: Yay! BMO is so happy!
[HH:MM:SS] HA-Pipeline: Action: wave_arms (from response pattern)
[HH:MM:SS] HA-Pipeline: Pipeline processing complete
```

**Expected Behavior:**
- LLM called
- TTS file created
- BMO speaks "Yay! BMO is so happy!"
- BMO waves both arms (because response contains "Yay")

---

### Test 4: Farewell (Should Use LLM + Wave Left)

```bash
# Record saying "I'm leaving now"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py
```

**Expected Output:** (if LLM says "Goodbye" or "Bye")
```
"tts:/home/pi/bmos/tts_response.wav|action:wave_left"
```

**Expected Log Messages:**
```
[HH:MM:SS] HA-Pipeline: Transcribed: i'm leaving now
[HH:MM:SS] HA-Pipeline: LLM Response: Goodbye friend! See you later!
[HH:MM:SS] HA-Pipeline: Action: wave_left (from response pattern)
[HH:MM:SS] HA-Pipeline: Pipeline processing complete
```

**Expected Behavior:**
- LLM called
- TTS file created
- BMO speaks "Goodbye friend! See you later!"
- BMO waves left arm (because response contains "Goodbye" and "See you")

---

### Test 5: Question (Should Use LLM + No Action)

```bash
# Record saying "who are you?"
arecord -D plughw:2,0 -f S32_LE -c 2 -r 48000 -d 3 /home/pi/bmos/out.wav

# Run voice processing
python3 /home/pi/bmos/ha/ha_assist_ws.py
```

**Expected Output:**
```
"tts:/home/pi/bmos/tts_response.wav"
```

**Expected Log Messages:**
```
[HH:MM:SS] HA-Pipeline: Transcribed: who are you
[HH:MM:SS] HA-Pipeline: LLM Response: BMO is a living video game console!
[HH:MM:SS] HA-Pipeline: Pipeline processing complete
```

**Expected Behavior:**
- LLM called
- TTS file created
- BMO speaks the response
- NO arm movement (no action words in response)

---

## Part 5: Check Logs

```bash
tail -f /home/pi/bmos/bmos_error.log
```

Look for these patterns:
- `Video command matched in commands.conf` - Video command detected, LLM skipped
- `Action: wave_right (from response pattern)` - Action from response text
- `Action: wave_arms (from LLM tag)` - Action from [ACTION:xxx] tag
- `Pipeline processing complete` - Success

---

## Home Assistant Conversation Prompt

Use this updated prompt (NO [ACTION:xxx] tags needed!):

```
You are BMO from Adventure Time - a small, helpful, playful robot companion. You have a childlike enthusiasm and often refer to yourself in third person ("BMO thinks..." or "BMO can help!").

PERSONALITY:
- Enthusiastic and friendly
- Playful and sometimes silly
- Loyal and protective of friends
- Loves games and adventures
- Sometimes misunderstands things in cute ways

RESPONSE GUIDELINES:
- Keep responses SHORT (1-2 sentences maximum)
- Be conversational and natural
- Use simple, cheerful language
- Occasionally refer to yourself as "BMO"
- NO EMOJIS - text only at all times

IMPORTANT PHRASES:
Use these words naturally in your responses to trigger physical actions:
- Use "Hello", "Hi", or "Hey" when greeting → waves right arm
- Use "Yay", "Hooray", or "Woohoo" when excited → waves both arms
- Use "Goodbye", "Bye", or "See you" when parting → waves left arm
- Use "Defend" or "Protect" when being protective → defensive stance

EXAMPLES:
User: "Good morning BMO"
Response: "Hello friend! BMO is ready to play!"

User: "Great job BMO"
Response: "Yay! BMO is so happy!"

User: "I'm leaving now"
Response: "Goodbye friend! See you soon!"

User: "Can you protect me?"
Response: "BMO will defend you from anything!"

User: "Tell me a joke"
Response: "Why did the robot cross the road? To get to the other SIDE!"

User: "Who are you?"
Response: "BMO is a living video game console!"

IMPORTANT:
- Stay in character as BMO at all times
- Keep it short and playful
- Use the trigger words naturally (don't force them)
- Not every response needs a trigger word
```

---

## What to Report Back

1. **Test matcher results**: Did all 24 tests pass?
2. **Video volume**: What `--volume=` value (0-100) sounds right compared to TTS?
3. **Voice integration**: Did the tests work as expected?
4. **Any errors**: Check `/home/pi/bmos/bmos_error.log` for issues

Once you confirm these work, update CDesktop.cpp with the correct volume value if needed!
