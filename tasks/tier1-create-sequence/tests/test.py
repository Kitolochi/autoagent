"""Verify the agent created a sequence named 'Test Sequence' via trajectory inspection."""
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

    # Check 1: create_sequence was called with name containing "Test Sequence"
    create_calls = find_tool_calls(steps, "create_sequence")
    if not create_calls:
        print("FAIL: create_sequence was never called")
        return 0.0

    name_match = False
    for call in create_calls:
        name_arg = call["arguments"].get("name", "")
        if "Test Sequence" in name_arg:
            name_match = True
            break

    if not name_match:
        names = [c["arguments"].get("name", "") for c in create_calls]
        print(f"FAIL: create_sequence called but not with 'Test Sequence'. Names used: {names}")
        return 0.0

    # Check 2: the tool call did not return an error
    for call in create_calls:
        if "Test Sequence" in call["arguments"].get("name", ""):
            content = call["content"].lower()
            if content.startswith("error"):
                print(f"FAIL: create_sequence returned an error: {call['content']}")
                return 0.0
            break

    # Check 3 (bonus): agent verified by calling list_sequences
    verify_calls = find_tool_calls(steps, "list_sequences")
    if verify_calls:
        print("PASS: create_sequence called with 'Test Sequence' and list_sequences verified")
        return 1.0

    print("PASS: create_sequence called with 'Test Sequence' (no verification step, partial credit)")
    return 0.8


if __name__ == "__main__":
    score = check()
    with open(REWARD_PATH, "w") as f:
        f.write(str(score))
    print(f"Score: {score}")
    sys.exit(0)
