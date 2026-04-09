# Tier-3 Implementation Guide

## Purpose

This guide provides implementation notes for creating `tier3_test.py` based on the tier-3 benchmark task definitions.

## File Structure

When implementing tier-3 tests, the test file should follow this structure:

```python
"""Tier-3 benchmark - complex production workflows requiring planning and composition."""
import asyncio
import json
import time
from pathlib import Path

from openai import AsyncOpenAI
from tools.premiere import _call_tool, close_session

# --- Config ---
MODEL = "claude-sonnet-4-6"
PROXY_BASE_URL = "http://127.0.0.1:8741/claude/v1"
MAX_TURNS = 40  # Tier-3 needs significantly more turns

SYSTEM_PROMPT = """You are a professional video editor working in Adobe Premiere Pro.
You have tools to interact with Premiere Pro. Use them to complete complex editing projects.
Plan your approach, break down tasks into steps, and verify your work as you go."""
```

## Tool Definitions

Tier-3 requires all available Premiere tools. Key additions beyond tier-1/2:

```python
TOOL_DEFS = [
    # ... tier-1/2 tools ...
    {"type": "function", "function": {"name": "add_marker", ...}},
    {"type": "function", "function": {"name": "trim_clip", ...}},
    {"type": "function", "function": {"name": "split_clip", ...}},
    {"type": "function", "function": {"name": "set_clip_opacity", ...}},
    {"type": "function", "function": {"name": "speed_change", ...}},
    {"type": "function", "function": {"name": "color_correct", ...}},
    {"type": "function", "function": {"name": "apply_effect", ...}},
    {"type": "function", "function": {"name": "adjust_audio_levels", ...}},
    {"type": "function", "function": {"name": "get_sequence_settings", ...}},
    # See tools/premiere.py for complete list
]
```

## Verification Helpers

Tier-3 requires deep structural verification:

```python
def verify_clip_count(trajectory: list[dict], track_index: int, min_clips: int) -> tuple[float, str]:
    """Verify minimum number of clips on a specific track."""
    for entry in trajectory:
        if entry.get("tool") == "get_full_sequence_info":
            result = json.loads(entry["result"])
            clips = result["videoTracks"][track_index]["clips"]
            if len(clips) >= min_clips:
                return 1.0, f"PASS: Track {track_index} has {len(clips)} clips (min {min_clips})"
    return 0.0, f"FAIL: Track {track_index} clip count not verified"

def verify_text_overlay_count(trajectory: list[dict], min_overlays: int) -> tuple[float, str]:
    """Count successful add_text_overlay calls."""
    count = sum(1 for e in trajectory 
                if e.get("tool") == "add_text_overlay" 
                and not e.get("result", "").lower().startswith("error"))
    if count >= min_overlays:
        return 1.0, f"PASS: {count} text overlays added (min {min_overlays})"
    return 0.0, f"FAIL: Only {count} text overlays, expected {min_overlays}"

def verify_markers(trajectory: list[dict], min_markers: int) -> tuple[float, str]:
    """Verify minimum number of markers placed."""
    count = sum(1 for e in trajectory 
                if e.get("tool") == "add_marker" 
                and not e.get("result", "").lower().startswith("error"))
    if count >= min_markers:
        return 1.0, f"PASS: {count} markers placed (min {min_markers})"
    return 0.0, f"FAIL: Only {count} markers, expected {min_markers}"

def verify_transitions(trajectory: list[dict], min_transitions: int) -> tuple[float, str]:
    """Verify transitions applied (via execute_extendscript or add_transition_to_clip)."""
    for entry in trajectory:
        if entry.get("tool") == "get_full_sequence_info":
            result = json.loads(entry["result"])
            # Check transitionCount in each track
            total_transitions = sum(track.get("transitionCount", 0) 
                                   for track in result["videoTracks"])
            if total_transitions >= min_transitions:
                return 1.0, f"PASS: {total_transitions} transitions (min {min_transitions})"
    return 0.0, f"FAIL: Transitions not verified or insufficient"

def verify_effect_applied(trajectory: list[dict], effect_name: str) -> tuple[float, str]:
    """Verify specific effect was applied to at least one clip."""
    for entry in trajectory:
        if entry.get("tool") == "apply_effect":
            args = entry.get("args", {})
            if args.get("effect_name") == effect_name:
                result = entry.get("result", "")
                if not result.lower().startswith("error"):
                    return 1.0, f"PASS: {effect_name} applied"
    return 0.0, f"FAIL: {effect_name} not applied"
```

## Test Template

Each tier-3 test should follow this pattern:

```python
async def test_multi_scene_story():
    print("\n=== Tier-3 Test: Multi-Scene Story ===")
    seq_name = f"Story_{int(time.time())}"
    
    # Load instruction from file
    instruction_path = Path(__file__).parent / "tasks" / "tier3-multi-scene-story" / "instruction.md"
    instruction = instruction_path.read_text()
    # Replace [timestamp] placeholder
    instruction = instruction.replace("[timestamp]", str(int(time.time())))
    
    traj = await run_agent(instruction)
    
    # Multi-criteria verification
    checks = [
        verify_clip_count(traj, track_index=0, min_clips=3),
        verify_text_overlay_count(traj, min_overlays=5),
        verify_markers(traj, min_markers=4),
        verify_transitions(traj, min_transitions=2),
    ]
    
    scores = [c[0] for c in checks]
    messages = [c[1] for c in checks]
    
    for msg in messages:
        print(f"  {msg}")
    
    # Pass if majority of checks pass
    final_score = sum(scores) / len(scores)
    if final_score >= 0.75:  # 75% of checks passing
        print(f"OVERALL: PASS ({final_score:.0%})")
        return 1.0
    else:
        print(f"OVERALL: FAIL ({final_score:.0%})")
        return 0.0
```

## Reading Instructions from Files

Instead of hardcoding instructions in test file:

```python
def load_task_instruction(task_name: str) -> str:
    """Load task instruction from tasks/ directory."""
    task_path = Path(__file__).parent / "tasks" / task_name / "instruction.md"
    if not task_path.exists():
        raise FileNotFoundError(f"Task instruction not found: {task_path}")
    
    instruction = task_path.read_text()
    
    # Replace timestamp placeholders
    timestamp = str(int(time.time()))
    instruction = instruction.replace("[timestamp]", timestamp)
    
    return instruction
```

## Recommended Test Order

Implement and run tests in this order:

1. **tier3-multi-scene-story** - Simplest tier-3, good starting point
2. **tier3-color-graded-montage** - Adds visual effects complexity
3. **tier3-podcast-edit** - Adds audio and multi-track complexity
4. **tier3-social-cutdown** - Adds format and pacing complexity
5. **tier3-trailer-assembly** - Most complex, capstone test

## Handling MCP Timeout

If tier-2 MCP timeout issues persist in tier-3:

1. **Increase timeout in MCP client** (if configurable)
2. **Add intermediate verification calls** to keep connection alive
3. **Break tasks into sub-tasks** with checkpoint verification
4. **Use streaming responses** if available in MCP HTTP transport

## Debugging Failed Tests

When a tier-3 test fails:

1. **Check trajectory** - Which tools were called?
2. **Check tool results** - Did any return errors?
3. **Inspect Premiere** - Open the project and sequence manually
4. **Verify timing** - Are clips/text at expected positions?
5. **Check track assignment** - Are elements on correct tracks?
6. **Review get_full_sequence_info** - Does structure match expectations?

## Success Criteria

A tier-3 test should pass if:
- ✅ All critical structural elements present (clips, text, markers)
- ✅ Timing is approximately correct (within 1s tolerance)
- ✅ Effects/transitions applied where specified
- ✅ Track organization is logical (base video, overlays, titles)
- ⚠️ Minor deviations acceptable (e.g., 4 text overlays instead of 5)

## Example Complete Test

```python
async def test_podcast_edit():
    print("\n=== Tier-3 Test: Podcast Edit ===")
    instruction = load_task_instruction("tier3-podcast-edit")
    traj = await run_agent(instruction)
    
    # Comprehensive verification
    checks = [
        ("Sequence created", verify_tool_success(traj, "create_sequence")),
        ("Clips added", verify_clip_count(traj, track_index=0, min_clips=1)),
        ("B-roll overlay", verify_clip_count(traj, track_index=1, min_clips=1)),
        ("Lower thirds", verify_text_overlay_count(traj, min_overlays=3)),
        ("Segment markers", verify_markers(traj, min_markers=4)),
        ("Audio adjusted", verify_tool_success(traj, "adjust_audio_levels")),
        ("Clip split", verify_tool_success(traj, "split_clip")),
    ]
    
    passed = sum(1 for _, (score, _) in checks if score > 0)
    total = len(checks)
    
    print(f"\n  Checks passed: {passed}/{total}")
    for name, (score, msg) in checks:
        status = "✓" if score > 0 else "✗"
        print(f"  {status} {name}: {msg}")
    
    # Pass if 80% of checks succeed
    if passed / total >= 0.8:
        print(f"\nOVERALL: PASS ({passed}/{total})")
        return 1.0
    else:
        print(f"\nOVERALL: FAIL ({passed}/{total})")
        return 0.0
```

## Next Steps

1. Copy structure from `tier2_test.py` as base
2. Increase MAX_TURNS to 40
3. Add tier-3 specific tools to TOOL_DEFS
4. Implement verification helpers (above)
5. Implement each test function using task instructions
6. Run tests and iterate on agent prompting
7. Document results and pass rates

## Related Files

- Task instructions: `tasks/tier3-*/instruction.md`
- Premiere tools: `tools/premiere.py`
- Tier-2 test (reference): `tier2_test.py`
- Tier-1 test (reference): `simple_test_v2.py`
