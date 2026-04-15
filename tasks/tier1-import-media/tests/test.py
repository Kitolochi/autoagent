"""Verify the agent imported media via trajectory inspection."""
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

    calls = find_tool_calls(steps, "import_media")
    if not calls:
        print("FAIL: import_media was never called")
        return 0.0

    success = False
    for call in calls:
        content = call["content"].lower()
        if not content.startswith("error"):
            success = True
            break

    if not success:
        print("FAIL: all import_media calls returned errors")
        return 0.0

    verify_calls = (
        find_tool_calls(steps, "list_project_items")
        + find_tool_calls(steps, "get_project_info")
    )
    if verify_calls:
        print("PASS: import_media succeeded and project state verified")
        return 1.0

    print("PASS: import_media succeeded (no verification step, partial credit)")
    return 0.8


if __name__ == "__main__":
    score = check()
    with open(REWARD_PATH, "w") as f:
        f.write(str(score))
    print(f"Score: {score}")
    sys.exit(0)
