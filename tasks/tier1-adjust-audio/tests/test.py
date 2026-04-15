"""Verify the agent adjusted audio levels via trajectory inspection."""
import json
import sys

TRAJECTORY_PATH = "/logs/agent/trajectory.json"
REWARD_PATH = "/logs/verifier/reward.txt"


def load_trajectory():
    with open(TRAJECTORY_PATH) as f:
        return json.load(f)


def find_tool_calls(steps, function_name):
    matches = []
    for step in steps:
        for tc in step.get("tool_calls", []):
            if tc.get("function_name") == function_name:
                obs = step.get("observation", {})
                results = obs.get("results", [])
                content = results[0].get("content", "") if results else ""
                matches.append({"arguments": tc.get("arguments", {}), "content": content})
    return matches


def check():
    try:
        traj = load_trajectory()
    except FileNotFoundError:
        print("FAIL: trajectory.json not found")
        return 0.0

    steps = traj.get("steps", [])
    if not steps:
        print("FAIL: trajectory has no steps")
        return 0.0

    calls = find_tool_calls(steps, "adjust_audio_levels")
    if not calls:
        print("FAIL: adjust_audio_levels was never called")
        return 0.0

    correct_volume = False
    success = False
    for call in calls:
        content = call["content"].lower()
        volume = call["arguments"].get("volume")
        if not content.startswith("error"):
            success = True
            if volume is not None and abs(float(volume) - (-6.0)) < 0.1:
                correct_volume = True

    if not success:
        print("FAIL: all adjust_audio_levels calls returned errors")
        return 0.0

    if not correct_volume:
        print("PASS: adjust_audio_levels succeeded but volume not -6.0 dB (partial credit)")
        return 0.6

    verify_calls = find_tool_calls(steps, "get_clip_properties")
    if verify_calls:
        print("PASS: adjust_audio_levels(-6.0 dB) succeeded and get_clip_properties verified")
        return 1.0

    print("PASS: adjust_audio_levels(-6.0 dB) succeeded (no verification step)")
    return 0.8


if __name__ == "__main__":
    score = check()
    with open(REWARD_PATH, "w") as f:
        f.write(str(score))
    print(f"Score: {score}")
    sys.exit(0)
