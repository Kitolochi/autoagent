"""Verify the agent added a text overlay with 'HELLO WORLD' via trajectory inspection."""
import json
import sys

TRAJECTORY_PATH = "/logs/agent/trajectory.json"
REWARD_PATH = "/logs/verifier/reward.txt"


def load_trajectory():
    with open(TRAJECTORY_PATH) as f:
        return json.load(f)


def find_tool_calls(steps, function_name):
    """Return all steps where the given function was called."""
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

    # Check 1: add_text_overlay was called
    overlay_calls = find_tool_calls(steps, "add_text_overlay")
    if not overlay_calls:
        print("FAIL: add_text_overlay was never called")
        return 0.0

    # Check 2: text argument contains "HELLO WORLD"
    best_score = 0.0
    for call in overlay_calls:
        args = call["arguments"]
        text = args.get("text", "")

        if "HELLO WORLD" not in text.upper():
            continue

        # Text matches, start scoring
        score = 0.4

        # Check the tool call did not error
        content = call["content"].lower()
        if content.startswith("error"):
            print(f"FAIL: add_text_overlay returned an error: {call['content']}")
            return 0.0

        # Check start_time (~5 seconds, allow tolerance)
        start_time = args.get("start_time", args.get("startTime", -1))
        if isinstance(start_time, (int, float)) and 4.5 <= start_time <= 5.5:
            score += 0.2

        # Check duration (~3 seconds, allow tolerance)
        duration = args.get("duration", -1)
        if isinstance(duration, (int, float)) and 2.5 <= duration <= 3.5:
            score += 0.2

        # Check track_index (should be 1)
        track = args.get("track_index", args.get("trackIndex", -1))
        if track == 1:
            score += 0.1

        # Bonus: agent verified with get_timeline_summary
        verify_calls = find_tool_calls(steps, "get_timeline_summary")
        if verify_calls:
            score += 0.1

        score = min(score, 1.0)
        best_score = max(best_score, score)

    if best_score == 0.0:
        texts = [c["arguments"].get("text", "") for c in overlay_calls]
        print(f"FAIL: add_text_overlay called but text did not contain 'HELLO WORLD'. Texts: {texts}")
        return 0.0

    print(f"PASS: add_text_overlay called with correct parameters (score={best_score})")
    return best_score


if __name__ == "__main__":
    score = check()
    with open(REWARD_PATH, "w") as f:
        f.write(str(score))
    print(f"Score: {score}")
    sys.exit(0)
