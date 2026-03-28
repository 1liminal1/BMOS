#!/usr/bin/env python3
"""
Home Assistant Voice Integration for BMOS with Fallback URLs
Tries primary HA URL, falls back to Nabu Casa remote URL
"""

import requests
import json
import sys
import os
import re
from datetime import datetime

# Import configuration from ha_config.py (not tracked in git)
# Copy ha_config.py.sample to ha_config.py and fill in your values
try:
    from ha_config import HA_URL, HA_TOKEN, PIPELINE_ID
    HA_URLS = [HA_URL]
    # Try to import remote URL for fallback
    try:
        from ha_config_remote import HA_URL as HA_REMOTE_URL
        HA_URLS.append(HA_REMOTE_URL)
    except ImportError:
        pass
except ImportError:
    print("ERROR: ha_config.py not found. Copy ha_config.py.sample to ha_config.py and fill in your values.", file=sys.stderr)
    sys.exit(1)

CONVERSATION_ID = "conversation.bmopi"

AUDIO_FILE = "/home/pi/bmos/out.wav"
TTS_OUTPUT = "/home/pi/bmos/tts_response.wav"
LOG_FILE = "/home/pi/bmos/bmos_error.log"

# Global to track which URL is working
ACTIVE_HA_URL = None

def log_msg(msg):
    """Log messages to error log"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] HA-Voice: {msg}\n")
    print(msg, file=sys.stderr)

def find_working_ha_url():
    """Try each HA URL until one works, return the working URL"""
    global ACTIVE_HA_URL
    
    for ha_url in HA_URLS:
        try:
            log_msg(f"Checking HA at {ha_url}/api/")
            response = requests.get(f"{ha_url}/api/",
                                  headers={"Authorization": f"Bearer {HA_TOKEN}"},
                                  timeout=3)
            if response.status_code == 200:
                log_msg(f"HA available at {ha_url}")
                ACTIVE_HA_URL = ha_url
                return ha_url
            else:
                log_msg(f"HA at {ha_url} returned {response.status_code}")
        except Exception as e:
            log_msg(f"HA check failed for {ha_url}: {e}")
            continue
    
    log_msg("No working HA URL found")
    return None

def check_ha_available():
    """Check if Home Assistant is reachable"""
    return find_working_ha_url() is not None

def process_with_assist_pipeline():
    """Use HA Assist Pipeline API for full STT→Conversation→TTS flow"""
    try:
        log_msg(f"Reading audio from {AUDIO_FILE}")
        with open(AUDIO_FILE, 'rb') as audio_file:
            audio_data = audio_file.read()

        log_msg(f"Sending to Assist Pipeline API")
        # Use the assist pipeline API which handles STT, conversation, and TTS
        response = requests.post(
            f"{ACTIVE_HA_URL}/api/assist_pipeline/run",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "audio/wav"
            },
            data=audio_data,
            timeout=30
        )

        log_msg(f"Assist Pipeline response status: {response.status_code}")
        if response.status_code == 200:
            # Parse the streaming response
            result = response.json()
            log_msg(f"Assist Pipeline result: {result}")

            # Extract text and response
            stt_text = result.get('stt', {}).get('text', '')
            response_text = result.get('response', {}).get('speech', {}).get('plain', {}).get('speech', '')

            log_msg(f"Transcribed: {stt_text}")
            log_msg(f"Response: {response_text}")

            return stt_text, response_text
        else:
            log_msg(f"Assist Pipeline failed: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        log_msg(f"Assist Pipeline error: {str(e)}")
        return None, None

def get_llm_response(text):
    """Send text to OpenAI conversation agent and get response"""
    try:
        payload = {
            "text": text,
            "language": "en",
            "agent_id": "conversation.bmopi"
        }

        response = requests.post(
            f"{ACTIVE_HA_URL}/api/conversation/process",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            response_text = data['response']['speech']['plain']['speech']
            log_msg(f"LLM Response: {response_text}")
            return response_text
        else:
            log_msg(f"LLM failed: {response.status_code}")
            return None

    except Exception as e:
        log_msg(f"LLM error: {str(e)}")
        return None

def parse_action(response_text):
    """Extract action from response text like [ACTION:wave_arms]"""
    match = re.search(r'\[ACTION:(\w+)\]', response_text)
    if match:
        action = match.group(1)
        # Remove action tag from text
        clean_text = re.sub(r'\[ACTION:\w+\]', '', response_text).strip()
        return action, clean_text
    return None, response_text

def get_tts_audio(text):
    """Get TTS audio from Home Assistant using BMO voice"""
    try:
        payload = {
            "message": text,
            "platform": "tts.piper",
            "options": {
                "voice": "en_US-bmo_voice-medium"
            }
        }

        response = requests.post(
            f"{ACTIVE_HA_URL}/api/tts_get_url",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            tts_url = data['url']  # Already a full URL from HA
            log_msg(f"TTS URL: {tts_url}")

            # Download TTS audio (longer timeout for BMO voice generation)
            audio_response = requests.get(tts_url, timeout=30)
            if audio_response.status_code == 200:
                # Save as MP3 first
                mp3_file = "/home/pi/bmos/tts_response.mp3"
                with open(mp3_file, 'wb') as f:
                    f.write(audio_response.content)
                log_msg(f"TTS MP3 saved to {mp3_file}")

                # Convert MP3 to WAV using ffmpeg
                import subprocess
                try:
                    subprocess.run([
                        'ffmpeg', '-y', '-i', mp3_file,
                        '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                        TTS_OUTPUT
                    ], check=True, capture_output=True)
                    log_msg(f"TTS converted to WAV: {TTS_OUTPUT}")
                    return True
                except subprocess.CalledProcessError as e:
                    log_msg(f"FFmpeg conversion failed: {e}")
                    return False

        log_msg(f"TTS failed: {response.status_code}")
        return False

    except Exception as e:
        log_msg(f"TTS error: {str(e)}")
        return False

def transcribe_with_google():
    """Use Google Speech Recognition for transcription"""
    try:
        import speech_recognition as sr

        log_msg("Using Google Speech Recognition")
        recognizer = sr.Recognizer()

        with sr.AudioFile(AUDIO_FILE) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)
        log_msg(f"Google transcribed: {text}")
        return text
    except Exception as e:
        log_msg(f"Google STT error: {e}")
        return None

def main():
    """Main processing flow - Google STT + HA Conversation"""
    log_msg("Starting HA voice processing (Google STT + HA Conversation)")

    # Step 1: Transcribe with Google
    transcribed_text = transcribe_with_google()
    if not transcribed_text:
        log_msg("Transcription failed")
        sys.exit(1)

    # Step 2: Check if HA is available
    if not check_ha_available():
        log_msg("Home Assistant not reachable, output Google result")
        print(f'"{transcribed_text}"')
        sys.exit(0)

    # Step 3: Get LLM response from HA
    llm_response = get_llm_response(transcribed_text)
    if not llm_response:
        log_msg("HA Conversation failed, output Google result")
        print(f'"{transcribed_text}"')
        sys.exit(0)

    # Step 4: Parse action from response
    action, clean_text = parse_action(llm_response)

    # Get TTS audio
    if not get_tts_audio(clean_text):
        # If TTS fails, just output text
        print(f'"{clean_text}"')
        sys.exit(0)

    # Output command for BMOS to parse
    # Format: tts:/path/to/audio|action:wave_arms
    if action:
        print(f'"tts:{TTS_OUTPUT}|action:{action}"')
    else:
        print(f'"tts:{TTS_OUTPUT}"')

    log_msg("HA voice processing complete")

if __name__ == "__main__":
    main()
