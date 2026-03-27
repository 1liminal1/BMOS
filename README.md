# BMOS
BMO Operating System - A real-life BMO (from Adventure Time) running on Raspberry Pi.

Forked from [BYOBMO/BMOS](https://github.com/BYOBMO/BMOS) with added **Raspberry Pi 5 support** and **Home Assistant Voice Assistant integration**.

## What's New

### Raspberry Pi 5 Support
- Replaced `omxplayer` with `mpv` for hardware-accelerated video playback
- Updated audio pipeline for Pi 5 compatibility
- Splash screen via `feh` during boot
- Crash fixes and startup reliability improvements

### Home Assistant Voice Assistant
BMO can now talk back using Home Assistant's voice pipeline:
1. Press the record button and speak
2. Audio is sent to Home Assistant (Whisper STT)
3. An LLM (e.g. OpenAI) generates a response in BMO's character
4. Piper TTS plays the response while BMO's face animates
5. The LLM can trigger arm movements via `[ACTION:xxx]` tags

Falls back to Google Speech Recognition if HA is unavailable.

See [HA_SETUP.md](HA_SETUP.md) for full setup instructions.

### Configuration
Sensitive config files are gitignored. Copy the samples and fill in your values:
```bash
cp ha/ha_config.py.sample ha/ha_config.py
cp ha/ha_config_remote.py.sample ha/ha_config_remote.py
# Edit both files with your HA URL, token, and pipeline ID
```

## License
Source code in this project is licensed under GNU General Public License v3.0

<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">Graphical and audio assets (Images, Icons, Videos, Audio) are licensed under <a href="http://creativecommons.org/licenses/by-nc-nd/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC-ND 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nd.svg?ref=chooser-v1"></a>

Fonts are licensed under their respective licenses. See fonts folder for specific licenses.

## Dependencies

### Required Packages
Make sure you have installed all of this first:
https://github.com/BYOBMO/BMO-Utils

```bash
sudo apt update
sudo apt-get install cmake
sudo apt-get install libsdl2-image-dev
sudo apt-get install libsdl2-ttf-dev
sudo apt-get install libsdl2-mixer-dev
sudo apt-get install libboost-all-dev
sudo apt-get install mpv  # Video playback (hardware accelerated on Pi 5)
```

### For Voice Recognition
```bash
sudo apt-get install python3-pip python3-requests
pip3 install SpeechRecognition
```

### For Home Assistant Voice (optional)
```bash
sudo apt-get install python3-requests python3-websockets
```

## Build
```bash
mkdir build
cd build
cmake ..
make
make install
```

## GPU
Set GPU memory to 256.
```
sudo raspi-config
```

Performance Options -> GPU Memory

## Manual Start
```bash
cd /home/pi/bmos
./bmos
```

## Auto Start
```bash
sudo cp /home/pi/bmos/scripts/10-bmos.sh /etc/profile.d
sudo chmod +r /etc/profile.d/10-bmos.sh
```

## Modes
BMO has two modes, face and desktop. In face mode you can press keys on the keyboard and they will execute the key mappings in your bmo.txt file (see below).

When in face mode you can double-click the green button (ALT key on the keyboard) to switch to desktop mode. You can also press the red button to start recording for voice recognition. Voice recognition must be turned on in the settings first. Hold the button until you are done speaking and BMO will attempt to match your command to what is in the commands.conf file.

In desktop mode you can use the DPad and the green button for mouse navigation and selection. Or, if you have a mouse plugged into the USB port, you can mouse as you would on a desktop PC. Holding the blue (triangle) button for a few seconds toggles between snap mode which makes the DPad cycle through the UI elements for easier selection. An icon in the upper right corner of the desktop shows which mode you are in.

## Key Mappings
Keys are mapped in the /home/pi/bmos/bmo.txt file.

Supported commands are face, mp4, system, random, and vg.

### face
The face command changes BMO's static face.
```
<key>:face:<filename>
```

Example:
```
1:face:bmo01.jpg
```
Will map keyboard "1" to to show "bmo01.jpg".

### mp4
The video command starts a video, usually a beemote.
```
<key>:mp4:<videofile>:<imagefile>
```

Example:
```
q:mp4:cn.mp4:bmo01.jpg
```
Will map keyboard "q" to play the mp4 file "cn.mp4" and then switch to "bmo01.jpg" when done.

### system
The "system" command will launch a script. Be careful with this. Starting the wrong script can damage your system.

Example:
```
Z:system:/home/pi/bmos/scripts/waveleft.sh
```

Executes the script that waves BMO's left arm.

### random
The random command creates a list of videos to be played randomly. They are played when you press up on BMO's DPad or if you turn on random videos in the settings.

Example:
```
random:hello.mp4
random:homies.mp4
random:ah.mp4
```

Adds hello.mp4, homies.mp4, and ah.mp4 to the random list.

### vg
The "vg" command will launch EmulationStation.
Example:
```
;:vg:videogames.mp4
```

This maps the semicolon ";" key to start EmulationStation. It will play videogames.mp4 before launching.

To get out of EmulationStation, you usually need to press F4. It depends on how you have your key bindings set up for EmulationStation.

## Project Documentation
- [HA_SETUP.md](HA_SETUP.md) - Home Assistant Voice Assistant setup guide
- [PI5_SYNC_NOTES.md](PI5_SYNC_NOTES.md) - Pi 5 migration notes
- [BOOT_FIX.md](BOOT_FIX.md) - Boot and startup troubleshooting
- [FALLBACK_SYSTEMS.md](FALLBACK_SYSTEMS.md) - Voice fallback system details
- [SHORTCUTS_REFERENCE.md](SHORTCUTS_REFERENCE.md) - Keyboard shortcuts reference

## Exiting
Alt-F4 will terminate the application and return to the CLI.
