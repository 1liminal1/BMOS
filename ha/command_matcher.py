#!/usr/bin/env python3
"""
Command matcher for BMOS commands.conf
Checks if transcribed text matches a video/system command
Also maps certain phrases to action commands
"""

import os
import re

COMMANDS_FILE = "/home/pi/bmos/commands.conf"

# Action mappings: phrase patterns in LLM RESPONSE -> action command
# These trigger actions when matched in the LLM's response text
ACTION_MAPPINGS = [
    # Wave arms actions - when LLM says these words
    (r'\b(yay|hooray|woohoo|celebrate)\b', 'wave_arms'),

    # Wave right arm - when LLM greets
    (r'\b(hi|hello|hey|greetings)\b', 'wave_right'),

    # Wave left arm
    (r'\b(goodbye|bye|see you)\b', 'wave_left'),

    # NOTE: Removed 'defend' action because:
    # - "defend me" command should ONLY trigger via commands.conf (video + choparm.sh)
    # - LLM responses containing "defend" shouldn't trigger the choparm script
]

def load_commands():
    """Load commands from commands.conf file"""
    commands = []

    if not os.path.exists(COMMANDS_FILE):
        return commands

    with open(COMMANDS_FILE, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse command format: phrase==action
            if '==' not in line:
                continue

            phrase, action = line.split('==', 1)

            # Check if it's a partial match (starts with ~)
            partial = phrase.startswith('~')
            if partial:
                phrase = phrase[1:]  # Remove ~

            # Include mp4, system, and launch commands (skip LLM for these)
            if action.startswith('mp4:') or action.startswith('system:') or action.startswith('launch:'):
                commands.append({
                    'phrase': phrase.lower(),
                    'action': action,
                    'partial': partial
                })

    return commands

def match_command(text, commands):
    """
    Check if text matches any video/system command
    Returns (matched, action) tuple
    """
    # Strip and lowercase
    text_lower = text.lower().strip()
    # Remove trailing punctuation that Whisper often adds
    text_lower = text_lower.rstrip('.,!?;:')

    # First try exact matches
    for cmd in commands:
        if not cmd['partial']:
            if text_lower == cmd['phrase']:
                return True, cmd['action']

    # Then try partial matches
    for cmd in commands:
        if cmd['partial']:
            if cmd['phrase'] in text_lower:
                return True, cmd['action']

    return False, None

def get_action_for_response(response_text):
    """
    Check if LLM response text should trigger an action
    Matches patterns in the LLM's response (not the user's input)
    Returns action name (e.g., 'wave_arms') if match found, None otherwise

    Example:
        - LLM responds "Hello friend!" → returns 'wave_right'
        - LLM responds "Yay!" → returns 'wave_arms'
        - LLM responds "Goodbye!" → returns 'wave_left'
    """
    text_lower = response_text.lower()

    for pattern, action in ACTION_MAPPINGS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return action

    return None

def check_video_command(text):
    """
    Check if transcribed text matches a video/system command
    Returns True if matches commands.conf, False otherwise
    """
    commands = load_commands()
    matched, action = match_command(text, commands)
    return matched
