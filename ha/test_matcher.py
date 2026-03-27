#!/usr/bin/env python3
"""
Test script for command_matcher.py
Tests video command matching and action mapping from LLM responses
"""

from command_matcher import check_video_command, get_action_for_response

print("=" * 70)
print("TEST 1: Video Command Matching (commands.conf)")
print("=" * 70)

# Test cases: (user transcription, should_match_video)
video_test_cases = [
    ("defend me", True),
    ("Defend Me", True),
    ("wave your arms", True),
    ("please wave your arms for me", True),
    ("hello", True),
    ("you're funny", True),
    ("what time is it", True),  # FIXED: This IS a video command in commands.conf
    ("turn on the lights", False),
    ("tell me a joke", False),
]

passed = 0
failed = 0

for phrase, should_match in video_test_cases:
    is_video = check_video_command(phrase)
    correct = is_video == should_match

    status = "✓ PASS" if correct else "✗ FAIL"
    if correct:
        passed += 1
    else:
        failed += 1

    print(f"{status}: '{phrase}'")
    if is_video:
        print(f"        → Video command (will skip LLM)")
    else:
        print(f"        → Not a video command (will use LLM)")
    print()

print(f"Video matching: {passed} passed, {failed} failed\n")

print("=" * 70)
print("TEST 2: Action Mapping (LLM response text)")
print("=" * 70)

# Test cases: (LLM response text, expected_action)
action_test_cases = [
    ("Hello friend!", "wave_right"),
    ("Hi there!", "wave_right"),
    ("Hey!", "wave_right"),
    ("Greetings!", "wave_right"),
    ("Yay! That's great!", "wave_arms"),
    ("Hooray!", "wave_arms"),
    ("Woohoo we did it!", "wave_arms"),
    ("Goodbye friend!", "wave_left"),
    ("Bye!", "wave_left"),
    ("See you later!", "wave_left"),
    ("I will defend you!", "defend"),
    ("Let me protect that!", "defend"),
    ("The time is 3:45 PM.", None),
    ("Let me help you with that.", None),
    ("I don't know.", None),
]

passed2 = 0
failed2 = 0

for response, expected_action in action_test_cases:
    action = get_action_for_response(response)
    correct = action == expected_action

    status = "✓ PASS" if correct else "✗ FAIL"
    if correct:
        passed2 += 1
    else:
        failed2 += 1

    print(f"{status}: '{response}'")
    if action:
        print(f"        → Action: {action}")
    else:
        print(f"        → No action")

    if not correct:
        print(f"        ⚠ Expected: {expected_action}, Got: {action}")
    print()

print(f"Action mapping: {passed2} passed, {failed2} failed\n")

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total: {passed + passed2} passed, {failed + failed2} failed")
print()
print("How it works:")
print("1. User says something → Whisper transcribes it")
print("2. Check if transcription matches commands.conf → if YES, skip LLM")
print("3. If NO, send to LLM for response")
print("4. Check LLM response text for action patterns (hello, yay, bye, etc.)")
print("5. Add action to TTS output if pattern matched")
