"""Verify the agent added a Cross Dissolve transition via trajectory inspection."""
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

    # Check 1: add_transition_to_clip was called
    transition_calls = find_tool_calls(steps, "add_transition_to_clip")
    if not transition_calls:
        print("FAIL: add_transition_to_clip was never called")
        return 0.0

    # Check 2: transition_name contains "dissolve" (case-insensitive)
    best_score = 0.0
    for call in transition_calls:
        args = call["arguments"]
        transition_name = args.get("transition_name", args.get("transitionName", ""))

        if "dissolve" not in transition_name.lower():
            continue

        # Transition name matches, start scoring
        score = 0.4

        # Check the tool call did not error
        content = call["content"].lower()
        if content.startswith("error"):
            print(f"FAIL: add_transition_to_clip returned an error: {call['content']}")
            return 0.0

        # Check track_index (should be 0)
        track = args.get("track_index", args.get("trackIndex", -1))
        if track == 0:
            score += 0.15

        # Check clip_index (should be 0)
        clip = args.get("clip_index", args.get("clipIndex", -1))
        if clip == 0:
            score += 0.15

        # Check duration (~1.0 seconds)
        duration = args.get("duration", -1)
        if isinstance(duration, (int, float)) and 0.5 <= duration <= 1.5:
            score += 0.15

        # Check position is "start"
        position = args.get("position", "")
        if position == "start":
            score += 0.05

        # Bonus: agent inspected timeline before/after
        inspect_before = find_tool_calls(steps, "get_active_sequence") or find_tool_calls(steps, "get_timeline_summary")
        if inspect_before:
            score += 0.1

        score = min(score, 1.0)
        best_score = max(best_score, score)

    if best_score == 0.0:
        names = [c["arguments"].get("transition_name", c["arguments"].get("transitionName", "")) for c in transition_calls]
        print(f"FAIL: add_transition_to_clip called but no 'dissolve' transition found. Names: {names}")
        return 0.0

    print(f"PASS: add_transition_to_clip called with Cross Dissolve (score={best_score})")
    return best_score


if __name__ == "__main__":
    score = check()
    with open(REWARD_PATH, "w") as f:
        f.write(str(score))
    print(f"Score: {score}")
    sys.exit(0)
