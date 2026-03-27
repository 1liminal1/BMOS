#!/usr/bin/env python3
"""
Home Assistant Voice Assistant Integration for BMOS using WebSocket Pipeline
Uses BMOpi assistant with faster-whisper STT and Piper BMO voice TTS
"""

import asyncio
import websockets
import json
import sys
import os
import wave
from datetime import datetime
import re
import subprocess
from command_matcher import check_video_command, get_action_for_response

# Import configuration from separate file (not committed to git)
# Use ha_config_remote.py if BMOS_REMOTE env var is set, otherwise use ha_config.py
try:
    if os.environ.get('BMOS_REMOTE'):
        from ha_config_remote import HA_URL, HA_WS_URL, HA_TOKEN, PIPELINE_ID
        print("Using REMOTE config (Nabu Casa)", file=sys.stderr)
    else:
        from ha_config import HA_URL, HA_WS_URL, HA_TOKEN, PIPELINE_ID
except ImportError as e:
    print(f"ERROR: Config file not found. Copy ha_config.py.sample to ha_config.py and fill in your credentials. ({e})", file=sys.stderr)
    sys.exit(1)

AUDIO_FILE = "/home/pi/bmos/out.wav"
TTS_OUTPUT = "/home/pi/bmos/tts_response.wav"
LOG_FILE = "/home/pi/bmos/bmos_error.log"

def log_msg(msg):
    """Log messages to error log"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] HA-Pipeline: {msg}\n")
    print(msg, file=sys.stderr)

def parse_action(response_text):
    """Extract action from response text like [ACTION:wave_arms]"""
    match = re.search(r'\[ACTION:(\w+)\]', response_text)
    if match:
        action = match.group(1)
        clean_text = re.sub(r'\[ACTION:\w+\]', '', response_text).strip()
        return action, clean_text
    return None, response_text

async def run_assist_pipeline():
    """Run the assist pipeline via WebSocket"""
    try:
        log_msg("Connecting to HA WebSocket...")

        async with websockets.connect(HA_WS_URL, ssl=True) as websocket:
            # Step 1: Receive auth_required message
            msg = await websocket.recv()
            log_msg(f"Received: {msg}")

            # Step 2: Send auth message
            auth_msg = {
                "type": "auth",
                "access_token": HA_TOKEN
            }
            await websocket.send(json.dumps(auth_msg))
            log_msg("Sent auth")

            # Step 3: Receive auth_ok
            msg = await websocket.recv()
            auth_response = json.loads(msg)
            log_msg(f"Auth response: {auth_response}")

            if auth_response.get("type") != "auth_ok":
                log_msg("Auth failed")
                return None, None

            # Step 4: Start assist pipeline
            pipeline_msg = {
                "type": "assist_pipeline/run",
                "id": 1,
                "start_stage": "stt",
                "end_stage": "tts",
                "pipeline": PIPELINE_ID,
                "input": {
                    "sample_rate": 16000
                }
            }
            await websocket.send(json.dumps(pipeline_msg))
            log_msg("Sent pipeline run request")

            # Step 5: Get result confirmation and then run-start event
            msg = await websocket.recv()
            result_msg = json.loads(msg)
            log_msg(f"Result: {result_msg}")

            # Now wait for run-start event
            handler_id = None
            while True:
                msg = await websocket.recv()
                event = json.loads(msg)
                log_msg(f"Event received: {event.get('type')}")

                if event.get("type") == "event":
                    event_data = event.get("event", {})
                    if event_data.get("type") == "run-start":
                        handler_id = event_data.get("data", {}).get("runner_data", {}).get("stt_binary_handler_id")
                        log_msg(f"Binary handler ID: {handler_id}")
                        break

            if not handler_id:
                log_msg("No binary handler ID received")
                return None, None

            # Step 6: Convert and send audio data
            log_msg(f"Reading audio from {AUDIO_FILE}")

            # Convert audio to 16kHz mono 16-bit PCM (required by pipeline)
            temp_audio = "/tmp/ha_pipeline_audio.wav"
            subprocess.run([
                'ffmpeg', '-y', '-i', AUDIO_FILE,
                '-ar', '16000', '-ac', '1', '-sample_fmt', 's16',
                temp_audio
            ], check=True, capture_output=True)
            log_msg(f"Audio converted to 16kHz mono")

            with wave.open(temp_audio, 'rb') as wf:
                # Read all audio data
                audio_data = wf.readframes(wf.getnframes())

            log_msg(f"Sending {len(audio_data)} bytes of audio")

            # Send audio in chunks prefixed with handler_id byte
            chunk_size = 8192
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                # Prefix with handler_id byte
                await websocket.send(bytes([handler_id]) + chunk)

            # Send empty chunk to signal end
            await websocket.send(bytes([handler_id]))
            log_msg("Finished sending audio")

            # Step 7: Receive events
            transcription = None
            response_text = None
            tts_media_id = None

            while True:
                msg = await asyncio.wait_for(websocket.recv(), timeout=30)
                event = json.loads(msg)

                event_type = event.get("event", {}).get("type")
                log_msg(f"Event: {event_type}")

                if event_type == "stt-end":
                    transcription = event["event"]["data"]["stt_output"]["text"]
                    log_msg(f"Transcribed: {transcription}")

                elif event_type == "intent-end":
                    response_text = event["event"]["data"]["intent_output"]["response"]["speech"]["plain"]["speech"]
                    log_msg(f"LLM Response: {response_text}")

                elif event_type == "tts-end":
                    tts_media_id = event["event"]["data"]["tts_output"]["media_id"]
                    log_msg(f"TTS media ID: {tts_media_id}")

                elif event_type == "run-end":
                    log_msg("Pipeline run complete")
                    break

                elif event_type == "error":
                    log_msg(f"Pipeline error: {event}")
                    break

            # Step 8: Download TTS audio
            if tts_media_id and response_text:
                # Extract the actual filename from media-source URL
                import urllib.parse
                if tts_media_id.startswith("media-source://"):
                    parts = tts_media_id.split("/")
                    filename = parts[-1] if len(parts) > 0 else tts_media_id
                else:
                    filename = tts_media_id

                tts_url = f"{HA_URL}/api/tts_proxy/{filename}"
                log_msg(f"Downloading TTS from {tts_url}")

                import requests
                headers = {"Authorization": f"Bearer {HA_TOKEN}"}
                response = requests.get(tts_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    mp3_file = "/home/pi/bmos/tts_response.mp3"
                    with open(mp3_file, 'wb') as f:
                        f.write(response.content)
                    log_msg(f"TTS MP3 saved to {mp3_file}")

                    # Convert to WAV (no volume adjustment)
                    subprocess.run([
                        'ffmpeg', '-y', '-i', mp3_file,
                        '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                        TTS_OUTPUT
                    ], check=True, capture_output=True)
                    log_msg(f"TTS converted to WAV: {TTS_OUTPUT}")

                    return transcription, response_text
                else:
                    log_msg(f"TTS download failed: {response.status_code}")
                    return transcription, response_text

            return transcription, response_text

    except asyncio.TimeoutError:
        log_msg("WebSocket timeout")
        return None, None
    except Exception as e:
        log_msg(f"Pipeline error: {str(e)}")
        import traceback
        log_msg(traceback.format_exc())
        return None, None

def main():
    """Main processing flow"""
    log_msg("Starting HA voice processing via WebSocket Pipeline")

    # Run async pipeline
    transcription, response_text = asyncio.run(run_assist_pipeline())

    if not transcription:
        log_msg("Pipeline failed")
        sys.exit(1)

    # Check if transcription matches a video/system command
    if check_video_command(transcription):
        log_msg("Video command matched in commands.conf")
        # Delete any old TTS file so it doesn't get played
        if os.path.exists(TTS_OUTPUT):
            os.remove(TTS_OUTPUT)
            log_msg("Removed old TTS file")
        # Output the video/system command instead of TTS
        print(f'"{transcription}"', flush=True)
        log_msg("Video command takes priority, skipping TTS")
        sys.exit(0)

    if not response_text:
        # No LLM response, just output transcription
        print(f'"{transcription}"')
        sys.exit(0)

    # Parse action from LLM response (e.g., [ACTION:wave_arms])
    llm_action, clean_text = parse_action(response_text)

    # Check if response text contains phrases that should trigger actions
    # (e.g., "Hello!" -> wave_right, "Yay!" -> wave_arms)
    response_action = get_action_for_response(clean_text)

    # Prefer explicit LLM action tag, but fall back to response text pattern
    final_action = llm_action if llm_action else response_action

    # Check if TTS file exists
    if os.path.exists(TTS_OUTPUT):
        # Output command for BMOS to parse
        if final_action:
            log_msg(f"Action: {final_action} (from {'LLM tag' if llm_action else 'response pattern'})")
            print(f'"tts:{TTS_OUTPUT}|action:{final_action}"', flush=True)
        else:
            print(f'"tts:{TTS_OUTPUT}"', flush=True)
        log_msg("Pipeline processing complete")
    else:
        # No TTS, just output text
        print(f'"{clean_text}"')
        log_msg("No TTS audio, output text only")

if __name__ == "__main__":
    main()
