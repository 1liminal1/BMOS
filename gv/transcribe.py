import speech_recognition as sr
import sys
from datetime import datetime
import wave
import audioop

def log_msg(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    with open('/home/pi/bmos/bmos_error.log', 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg, file=sys.stderr)

def convert_audio():
    with wave.open('/home/pi/bmos/out.wav', 'rb') as wf:
        nchannels, sampwidth, framerate, nframes, comptype, compname = wf.getparams()
        frames = wf.readframes(nframes)

        if nchannels == 2:
            frames = audioop.tomono(frames, sampwidth, 1, 1)

        if sampwidth == 4:
            frames = audioop.lin2lin(frames, 4, 2)

        if framerate != 16000:
            frames, _ = audioop.ratecv(frames, 2, 1, framerate, 16000, None)

        with wave.open('/home/pi/bmos/converted.wav', 'wb') as wfo:
            wfo.setnchannels(1)
            wfo.setsampwidth(2)
            wfo.setframerate(16000)
            wfo.writeframes(frames)

    return '/home/pi/bmos/converted.wav'

def check_command_exists(text):
    try:
        with open('/home/pi/bmos/commands.conf', 'r') as f:
            commands = f.readlines()
            commands = [c.strip() for c in commands if c.strip() and not c.strip().startswith('#')]

            for cmd in commands:
                if '==' in cmd:
                    cmd_text = cmd.split('==')[0].strip()
                    if not cmd_text.startswith('~') and cmd_text.lower() == text.lower():
                        return True

            for cmd in commands:
                if '==' in cmd:
                    cmd_text = cmd.split('==')[0].strip()
                    if cmd_text.startswith('~'):
                        cmd_text = cmd_text[1:]
                        if cmd_text.lower() in text.lower():
                            return True

        return False
    except:
        return True

r = sr.Recognizer()

try:
    log_msg("Starting transcription")
    converted_file = convert_audio()

    af = sr.AudioFile(converted_file)
    with af as source:
        log_msg("Reading audio file...")
        audio = r.record(source)

    try:
        log_msg("Starting recognition...")
        x = r.recognize_google(audio, show_all=False, language="en-AU")
        log_msg(f"Recognized: {x}")

        if not check_command_exists(x):
            log_msg("No matching command found - using default response")
            print('"what"')
        else:
            print(f'"{x}"')

    except sr.UnknownValueError:
        log_msg("No speech detected")
        print("No speech detected")
    except sr.RequestError as e:
        log_msg(f"Google service error: {str(e)}")
        print(f"Service error: {str(e)}")

except Exception as e:
    log_msg(f"Error: {str(e)}")
    print(f"Error: {str(e)}")
