"""Tier-2 benchmark - multi-step composite video editing workflows."""
import asyncio
import json
import time

from openai import AsyncOpenAI
from tools.premiere import _call_tool, close_session

# --- Config ---
MODEL = "claude-sonnet-4-6"
PROXY_BASE_URL = "http://127.0.0.1:8741/claude/v1"
MAX_TURNS = 20  # Tier-2 needs more turns for multi-step workflows

SYSTEM_PROMPT = """You are a professional video editor working in Adobe Premiere Pro.
You have tools to interact with Premiere Pro. Use them to complete complex editing tasks.
Break down the task into steps, call tools one at a time, and verify your work."""

client = AsyncOpenAI(base_url=PROXY_BASE_URL, api_key="not-needed")

# --- Tool definitions ---
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
    """Run the agent and return conversation trajectory."""
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


def check_tools_called(trajectory: list[dict], required_tools: list[str]) -> tuple[float, str]:
    """Check if all required tools were called successfully."""
    called = set()
    errors = []

    for entry in trajectory:
        tool = entry.get("tool")
        if tool in required_tools:
            result = entry.get("result", "")
            if not result.lower().startswith("error"):
                called.add(tool)
            else:
                errors.append(f"{tool}: {result[:60]}")

    missing = set(required_tools) - called
    if missing:
        return 0.0, f"FAIL: missing {missing}, errors: {errors}"
    return 1.0, f"PASS: all required tools called ({required_tools})"


# --- Test 1: Basic Edit ---
async def test_basic_edit():
    print("\n=== Test 1: Basic Edit (Sequence + Clip + Text + Transition) ===")
    seq_name = f"BasicEdit_{int(time.time())}"
    instruction = f"""Create a basic edited sequence:
1. Create a sequence named "{seq_name}"
2. Add a Bars and Tone clip to video track 0 at time 0
3. Add a text overlay "INTRO" on track 1, starting at 1 second, duration 2 seconds
4. Add a Cross Dissolve transition to the start of the Bars and Tone clip using execute_extendscript"""

    traj = await run_agent(instruction)
    required = ["create_sequence", "create_bars_and_tone", "add_to_timeline", "add_text_overlay", "execute_extendscript"]
    score, msg = check_tools_called(traj, required)
    print(msg)
    return score


# --- Test 2: Two Clips with Transition ---
async def test_two_clips_transition():
    print("\n=== Test 2: Two Clips with Transition Between ===")
    seq_name = f"TwoClips_{int(time.time())}"
    instruction = f"""Create a sequence with two clips and a transition:
1. Create a sequence named "{seq_name}"
2. Create a Bars and Tone clip and add it to track 0 at 0 seconds
3. Create another Bars and Tone clip and add it to track 0 at 5 seconds
4. Add a Cross Dissolve transition between the clips using execute_extendscript"""

    traj = await run_agent(instruction)
    # Check for create_bars_and_tone called at least twice
    bars_calls = sum(1 for e in traj if e.get("tool") == "create_bars_and_tone")
    add_calls = sum(1 for e in traj if e.get("tool") == "add_to_timeline")

    if bars_calls >= 2 and add_calls >= 2:
        score, msg = check_tools_called(traj, ["create_sequence", "execute_extendscript"])
        if score > 0:
            print(f"PASS: created 2 clips, added to timeline, and applied transition")
            return 1.0
    print(f"FAIL: bars_calls={bars_calls}, add_calls={add_calls}")
    return 0.0


# --- Test 3: Titled Sequence ---
async def test_titled_sequence():
    print("\n=== Test 3: Titled Sequence (Multiple Text Overlays) ===")
    seq_name = f"TitledSeq_{int(time.time())}"
    instruction = f"""Create a titled sequence:
1. Create a sequence named "{seq_name}"
2. Add a Bars and Tone clip to track 0 starting at 0
3. Add text overlay "My Video Project" on track 2, from 0-3 seconds
4. Add text overlay "By AutoAgent" on track 2, from 3.5-5.5 seconds"""

    traj = await run_agent(instruction)
    text_calls = sum(1 for e in traj if e.get("tool") == "add_text_overlay")

    if text_calls >= 2:
        score, msg = check_tools_called(traj, ["create_sequence", "create_bars_and_tone", "add_to_timeline"])
        if score > 0:
            print(f"PASS: created sequence with 2 text overlays")
            return 1.0
    print(f"FAIL: text_calls={text_calls}")
    return 0.0


async def main():
    print("=" * 60)
    print("Tier-2 Video Editor Benchmark")
    print("Multi-step composite workflows")
    print("=" * 60)

    scores = []
    tests = [
        ("basic_edit", test_basic_edit),
        ("two_clips_transition", test_two_clips_transition),
        ("titled_sequence", test_titled_sequence),
    ]

    for name, test_fn in tests:
        try:
            score = await test_fn()
            scores.append((name, score))
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
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
