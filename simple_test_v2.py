"""Simple tier-1 benchmark - direct API loop, no SDK middleman."""
import asyncio
import json
import time
from pathlib import Path

from openai import AsyncOpenAI
from tools.premiere import _call_tool, close_session

# --- Config ---
MODEL = "claude-sonnet-4-6"
PROXY_BASE_URL = "http://127.0.0.1:8741/claude/v1"
MAX_TURNS = 10

SYSTEM_PROMPT = """You are a professional video editor working in Adobe Premiere Pro.
You have tools to interact with Premiere Pro. Use them to complete the task.
Call tools one at a time. Always verify your work after making changes."""

client = AsyncOpenAI(base_url=PROXY_BASE_URL, api_key="not-needed")

# --- Tool definitions for the API ---
TOOL_DEFS = [
    {"type": "function", "function": {"name": "get_project_info", "description": "Get info about the current Premiere Pro project.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_active_sequence", "description": "Get info about the active sequence.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_timeline_summary", "description": "Get a summary of all tracks and clips on the active timeline.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "list_sequences", "description": "List all sequences in the project.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_full_sequence_info", "description": "Get complete sequence info including clip node IDs, transitions, and effects.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "create_sequence", "description": "Create a new sequence.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "add_text_overlay", "description": "Add a text overlay to the active sequence using a Basic Title MOGRT.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "track_index": {"type": "number"}, "start_seconds": {"type": "number"}, "duration_seconds": {"type": "number"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "create_bars_and_tone", "description": "Create a Bars and Tone media item in the project.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "add_to_timeline", "description": "Add a project item to the timeline.", "parameters": {"type": "object", "properties": {"item_id": {"type": "string", "description": "Node ID or name of the project item"}, "track_index": {"type": "number"}, "start_seconds": {"type": "number"}}, "required": ["item_id"]}}},
    {"type": "function", "function": {"name": "execute_extendscript", "description": "Execute custom ExtendScript (ES3 syntax) in Premiere Pro. Helpers: __secondsToTicks(s), __ticksToSeconds(t), __result(data), __error(msg). Must end with return __result({}) or return __error(''). Use app.enableQE() for QE DOM. Use var not let/const.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout_ms": {"type": "number"}}, "required": ["code"]}}},
]


async def call_premiere_tool(name: str, args: dict) -> str:
    """Route tool call to Premiere MCP."""
    return await _call_tool(name, args)


async def run_agent(instruction: str) -> list[dict]:
    """Run a simple tool-calling loop and return the conversation history."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
    ]
    trajectory = []

    for turn in range(MAX_TURNS):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFS,
            max_tokens=2048,
            parallel_tool_calls=False,
        )

        choice = response.choices[0]
        msg = choice.message

        if msg.content:
            trajectory.append({"role": "assistant", "content": msg.content})

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            break

        assistant_msg = {"role": "assistant", "content": msg.content or "", "tool_calls": []}
        for tc in msg.tool_calls:
            assistant_msg["tool_calls"].append({
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            })
        messages.append(assistant_msg)

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"  -> {fn_name}({json.dumps(fn_args, indent=None)[:80]})")

            result = await call_premiere_tool(fn_name, fn_args)
            print(f"     = {result[:120]}")

            trajectory.append({
                "tool": fn_name,
                "args": fn_args,
                "result": result,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return trajectory


def check_trajectory(trajectory: list[dict], tool_name: str) -> tuple[float, str]:
    """Check if a specific tool was called successfully (any call, not just first)."""
    last_error = None
    for entry in trajectory:
        if entry.get("tool") == tool_name:
            result = entry.get("result", "")
            if not result.lower().startswith("error"):
                return 1.0, f"PASS: {tool_name} succeeded"
            else:
                last_error = result
    if last_error:
        return 0.0, f"FAIL: {last_error[:120]}"
    return 0.0, f"FAIL: {tool_name} was never called"


def check_trajectory_any(trajectory: list[dict], tool_names: list[str]) -> tuple[float, str]:
    """Check if ANY of the listed tools was called successfully."""
    for name in tool_names:
        score, msg = check_trajectory(trajectory, name)
        if score > 0:
            return score, msg
    return 0.0, f"FAIL: none of {tool_names} called successfully"


# --- Test 1: Create Sequence ---
async def test_create_sequence():
    print("\n=== Test 1: Create Sequence ===")
    seq_name = f"TestSeq_{int(time.time())}"
    instruction = f'Create a new sequence named "{seq_name}" in Premiere Pro. Steps: 1) get_project_info, 2) create_sequence with name "{seq_name}", 3) list_sequences to verify.'

    traj = await run_agent(instruction)
    score, msg = check_trajectory(traj, "create_sequence")
    print(msg)
    return score


# --- Test 2: Add text overlay ---
async def test_add_text_overlay():
    print("\n=== Test 2: Add Text Overlay ===")
    instruction = 'Add a text overlay saying "HELLO WORLD" to the active timeline on track_index 1, at start_seconds 5, with duration_seconds 3. Steps: 1) get_active_sequence, 2) add_text_overlay with text "HELLO WORLD", track_index 1, start_seconds 5, duration_seconds 3, 3) get_timeline_summary to verify.'

    traj = await run_agent(instruction)
    score, msg = check_trajectory(traj, "add_text_overlay")
    print(msg)
    return score


# --- Test 3: Add Clip to Timeline ---
async def test_add_clip_to_timeline():
    print("\n=== Test 3: Add Clip to Timeline ===")
    instruction = """Add a Bars and Tone clip to the active timeline. Steps:
1. Call create_bars_and_tone to create the media item.
2. Use add_to_timeline to add it to track 0 at start_seconds 0.
3. Call get_timeline_summary to verify the clip appears on track 0."""

    traj = await run_agent(instruction)
    score1, msg1 = check_trajectory(traj, "create_bars_and_tone")
    score2, msg2 = check_trajectory(traj, "add_to_timeline")
    if score1 > 0 and score2 > 0:
        print("PASS: both create_bars_and_tone and add_to_timeline succeeded")
        return 1.0
    print(f"FAIL: {msg1}, {msg2}")
    return 0.0


# --- Test 4: Add Transition ---
async def test_add_transition():
    print("\n=== Test 4: Add Transition ===")
    instruction = """Add a Cross Dissolve transition to the first video clip on the active timeline. Steps:
1. Call get_full_sequence_info to find the first clip on videoTracks[0] and its nodeId.
2. Use execute_extendscript to add the transition via QE DOM (since add_transition_to_clip has a bug):
   - app.enableQE();
   - var qeSeq = qe.project.getActiveSequence();
   - var track = qeSeq.getVideoTrackAt(0);
   - var clip = track.getItemAt(0);
   - clip.addTransition(qe.project.getVideoTransitionByName("Cross Dissolve"), true, "30");
   - return __result({added: true, clipName: clip.name});
3. Call get_full_sequence_info again to verify transitionCount > 0 on track 0."""

    traj = await run_agent(instruction)
    for entry in traj:
        if entry.get("tool") == "execute_extendscript":
            result = entry.get("result", "")
            if "added" in result.lower() and not result.lower().startswith("error"):
                print("PASS: transition added via execute_extendscript")
                return 1.0
    score, msg = check_trajectory_any(traj, ["execute_extendscript"])
    print(msg)
    return score


async def main():
    print("=" * 60)
    print("Tier-1 Video Editor Benchmark")
    print("=" * 60)

    scores = []
    tests = [
        ("create_sequence", test_create_sequence),
        ("add_text_overlay", test_add_text_overlay),
        ("add_clip", test_add_clip_to_timeline),
        ("add_transition", test_add_transition),
    ]

    for name, test_fn in tests:
        try:
            score = await test_fn()
            scores.append((name, score))
        except Exception as e:
            print(f"ERROR: {e}")
            scores.append((name, 0.0))

    await close_session()

    print("\n" + "=" * 60)
    for name, score in scores:
        status = "PASS" if score > 0 else "FAIL"
        print(f"  {status}: {name}")
    passed = sum(1 for _, s in scores if s > 0)
    print(f"\nResults: {passed}/{len(scores)} passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
