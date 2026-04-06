# Video Editor Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the AutoAgent harness into a Premiere Pro + After Effects video editor agent with graduated benchmark tasks.

**Architecture:** The agent operates host-side (no Docker) using the OpenAI Agents SDK with `OpenAIChatCompletionsModel` routed through ccproxy. It calls Premiere Pro via MCP tools and After Effects via ExtendScript bridge. Benchmarks test editing operations of increasing complexity.

**Tech Stack:** Python 3.12+, openai-agents SDK, ccproxy (Claude Sonnet 4.6), Premiere Pro MCP, httpx (for MCP HTTP calls), Harbor (benchmark framework)

**Prerequisites:** ccproxy running at localhost:8741, Premiere Pro running with MCP bridge active

---

### Task 1: Extract and compress knowledge base

**Files:**
- Create: `knowledge/techniques.md`
- Create: `knowledge/ae-gotchas.md`

**Step 1: Create knowledge directory**

```bash
mkdir -p knowledge
```

**Step 2: Write compressed technique reference**

Create `knowledge/techniques.md` — a compressed version of the top-20 video engagement techniques from `video-engagement-techniques`. Pull from the catalog. Keep each technique to 2-3 lines: name, when to use, key parameters. Target under 3000 tokens so it fits in a system prompt.

Source repo: `https://github.com/Kitolochi/video-engagement-techniques`
Read: `catalog/video-teardown-takeaways.md` for the technique list.

**Step 3: Write compressed AE gotchas**

Create `knowledge/ae-gotchas.md` — compressed version of critical gotchas from `ae-extendscript-patterns`. Focus on the patterns that cause silent failures (TextDocument constructor, Drop Shadow naming, opacity range inconsistencies, mask API quirks).

Source repo: `https://github.com/Kitolochi/ae-extendscript-patterns`
Read: `gotchas.md`, `expressions.md`, `bridge-architecture.md`

**Step 4: Commit**

```bash
git add knowledge/
git commit -m "feat(knowledge): add compressed technique and AE gotcha references"
```

---

### Task 2: Create Premiere MCP tool wrappers

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/premiere.py`

The agent needs to call Premiere MCP tools. Since the agent runs via the OpenAI Agents SDK (not Claude Code), we need thin Python wrappers that make HTTP calls to the Premiere MCP server.

**Step 1: Check Premiere MCP server connectivity**

The Premiere MCP runs as a local server. Find its port/endpoint:

```bash
# Check if Premiere MCP is accessible — common ports are 3000, 8080, or configured in the MCP bridge
curl -s http://localhost:3000/health 2>&1 || echo "not on 3000"
curl -s http://localhost:8080/health 2>&1 || echo "not on 8080"
```

Alternatively, the agent may need to call the MCP tools through Claude Code's MCP infrastructure. In that case, the tools should shell out to a helper script that invokes the MCP. Research the exact mechanism.

**Step 2: Create tools/__init__.py**

```python
```

**Step 3: Create tools/premiere.py with core tool functions**

Create functions decorated with `@function_tool` from the openai-agents SDK. Each function wraps a Premiere MCP operation.

Start with these essential tools (the minimum set needed for Tier 1 tasks):

```python
"""Premiere Pro tools for the video editor agent."""

from __future__ import annotations

import json
import subprocess

from agents import function_tool


async def _call_premiere_mcp(tool_name: str, args: dict) -> str:
    """Call a Premiere Pro MCP tool via the bridge.

    This shells out to a helper that sends the MCP call to Premiere.
    The exact transport depends on how the Premiere MCP bridge is exposed.
    """
    # Implementation depends on Premiere MCP transport discovery in Step 1.
    # Option A: HTTP to local MCP server
    # Option B: Shell out to a node script that calls the CEP panel
    # Option C: Write to the file-polling bridge directory
    raise NotImplementedError("Fill in after discovering MCP transport")


@function_tool
async def premiere_get_project_info() -> str:
    """Get current Premiere Pro project info: name, path, sequences."""
    return await _call_premiere_mcp("get_project_info", {})


@function_tool
async def premiere_get_active_sequence() -> str:
    """Get the active sequence: name, duration, track count, video/audio tracks."""
    return await _call_premiere_mcp("get_active_sequence", {})


@function_tool
async def premiere_get_timeline_summary() -> str:
    """Get a summary of all clips on the active timeline with positions and durations."""
    return await _call_premiere_mcp("get_timeline_summary", {})


@function_tool
async def premiere_import_media(file_path: str) -> str:
    """Import a media file (video, audio, image) into the Premiere project."""
    return await _call_premiere_mcp("import_media", {"filePath": file_path})


@function_tool
async def premiere_create_sequence(name: str, preset: str = "") -> str:
    """Create a new sequence in the project. Preset is optional."""
    return await _call_premiere_mcp("create_sequence", {"name": name, "preset": preset})


@function_tool
async def premiere_add_to_timeline(
    item_name: str, track_index: int = 0, start_time: float = 0.0
) -> str:
    """Add a project item to the timeline at a specific track and time (seconds)."""
    return await _call_premiere_mcp(
        "add_to_timeline",
        {"itemName": item_name, "trackIndex": track_index, "startTime": start_time},
    )


@function_tool
async def premiere_add_text_overlay(
    text: str, start_time: float = 0.0, duration: float = 3.0,
    x: float = 0.5, y: float = 0.5, font_size: float = 60.0,
) -> str:
    """Add a text overlay to the timeline."""
    return await _call_premiere_mcp(
        "add_text_overlay",
        {"text": text, "startTime": start_time, "duration": duration,
         "x": x, "y": y, "fontSize": font_size},
    )


@function_tool
async def premiere_add_transition(
    clip_index: int, transition_name: str = "Cross Dissolve",
    duration: float = 1.0,
) -> str:
    """Add a transition to a clip. Default is Cross Dissolve."""
    return await _call_premiere_mcp(
        "add_transition_to_clip",
        {"clipIndex": clip_index, "transitionName": transition_name,
         "duration": duration},
    )


@function_tool
async def premiere_apply_effect(clip_index: int, effect_name: str) -> str:
    """Apply a video effect to a clip by index."""
    return await _call_premiere_mcp(
        "apply_effect",
        {"clipIndex": clip_index, "effectName": effect_name},
    )


@function_tool
async def premiere_adjust_audio_levels(track_index: int, level_db: float) -> str:
    """Set audio level in dB for a track."""
    return await _call_premiere_mcp(
        "adjust_audio_levels",
        {"trackIndex": track_index, "levelDb": level_db},
    )


@function_tool
async def premiere_get_clip_properties(track_index: int, clip_index: int) -> str:
    """Get detailed properties of a specific clip."""
    return await _call_premiere_mcp(
        "get_clip_properties",
        {"trackIndex": track_index, "clipIndex": clip_index},
    )


@function_tool
async def premiere_list_clip_effects(track_index: int, clip_index: int) -> str:
    """List all effects applied to a specific clip."""
    return await _call_premiere_mcp(
        "list_clip_effects",
        {"trackIndex": track_index, "clipIndex": clip_index},
    )


@function_tool
async def premiere_get_total_clip_count() -> str:
    """Get the total number of clips in the active sequence."""
    return await _call_premiere_mcp("get_total_clip_count", {})


def get_all_premiere_tools() -> list:
    """Return all Premiere tools for registration with the agent."""
    return [
        premiere_get_project_info,
        premiere_get_active_sequence,
        premiere_get_timeline_summary,
        premiere_import_media,
        premiere_create_sequence,
        premiere_add_to_timeline,
        premiere_add_text_overlay,
        premiere_add_transition,
        premiere_apply_effect,
        premiere_adjust_audio_levels,
        premiere_get_clip_properties,
        premiere_list_clip_effects,
        premiere_get_total_clip_count,
    ]
```

**Step 4: Commit**

```bash
git add tools/
git commit -m "feat(tools): add Premiere MCP tool wrappers for agent"
```

---

### Task 3: Create knowledge lookup tool

**Files:**
- Create: `tools/knowledge.py`

**Step 1: Write the knowledge lookup tool**

```python
"""Knowledge base lookup tools for the video editor agent."""

from __future__ import annotations

from pathlib import Path

from agents import function_tool

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


@function_tool
async def lookup_technique(query: str) -> str:
    """Search the video technique knowledge base for a technique by name or use case.

    Returns matching technique descriptions from the catalog.
    """
    techniques_path = KNOWLEDGE_DIR / "techniques.md"
    if not techniques_path.exists():
        return "ERROR: techniques.md not found in knowledge/"
    content = techniques_path.read_text(encoding="utf-8")
    query_lower = query.lower()
    sections = content.split("\n## ")
    matches = [s for s in sections if query_lower in s.lower()]
    if matches:
        return "\n---\n".join(matches[:3])
    return f"No techniques matched '{query}'. Available sections:\n" + "\n".join(
        s.split("\n")[0] for s in sections if s.strip()
    )


@function_tool
async def lookup_ae_pattern(query: str) -> str:
    """Search After Effects ExtendScript patterns and gotchas.

    Returns relevant patterns, workarounds, and known issues.
    """
    gotchas_path = KNOWLEDGE_DIR / "ae-gotchas.md"
    if not gotchas_path.exists():
        return "ERROR: ae-gotchas.md not found in knowledge/"
    content = gotchas_path.read_text(encoding="utf-8")
    query_lower = query.lower()
    sections = content.split("\n## ")
    matches = [s for s in sections if query_lower in s.lower()]
    if matches:
        return "\n---\n".join(matches[:3])
    return f"No patterns matched '{query}'. Available sections:\n" + "\n".join(
        s.split("\n")[0] for s in sections if s.strip()
    )


def get_all_knowledge_tools() -> list:
    """Return all knowledge tools for registration with the agent."""
    return [lookup_technique, lookup_ae_pattern]
```

**Step 2: Commit**

```bash
git add tools/knowledge.py
git commit -m "feat(tools): add knowledge base lookup tools"
```

---

### Task 4: Rewrite agent.py for video editing

**Files:**
- Modify: `agent.py:28-80` (editable harness section only)

**Step 1: Read current agent.py to confirm the editable boundary**

The editable section is lines 28-80 (above `FIXED ADAPTER BOUNDARY`).

**Step 2: Rewrite the editable section**

Replace `SYSTEM_PROMPT`, `create_tools`, `create_agent`, and `run_task` with the video editor versions:

- `SYSTEM_PROMPT` — Professional video editor role, Inspect→Plan→Execute→Verify workflow, compressed technique reference loaded from `knowledge/techniques.md`
- `create_tools` — Returns Premiere tools + knowledge tools + run_shell (kept for general commands)
- `create_agent` — Builds the agent with all tools
- `run_task` — Same structure, may need to skip environment.exec since tasks run host-side

Key: The agent does NOT use Harbor's Docker environment for execution. It talks to Premiere/AE directly on the host. But it still needs to work within the Harbor adapter boundary for benchmarking. The `environment` parameter from Harbor can be ignored for Premiere operations — the tools call the MCP directly.

Load the system prompt from file at import time to keep agent.py clean:

```python
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

def _load_knowledge(filename: str) -> str:
    path = KNOWLEDGE_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""

TECHNIQUE_REF = _load_knowledge("techniques.md")
AE_GOTCHAS = _load_knowledge("ae-gotchas.md")

SYSTEM_PROMPT = f"""You are a professional video editor working in Adobe Premiere Pro and After Effects.

## Your Workflow
1. INSPECT — Check the current project and timeline state before making changes
2. PLAN — Decide what edits to make and in what order
3. EXECUTE — Make the edits using your tools
4. VERIFY — Check the result matches the task requirements

## Rules
- Always call premiere_get_active_sequence or premiere_get_timeline_summary before editing
- After every edit, verify the change took effect
- For titles and motion graphics, consider whether AE or Premiere text is more appropriate
- Use transitions between clips — never leave hard cuts unless the task specifies them

## Technique Reference
{TECHNIQUE_REF}

## After Effects Gotchas
{AE_GOTCHAS}
"""
```

**Step 3: Verify agent imports**

```bash
uv run python -c "from agent import AutoAgent; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add agent.py
git commit -m "feat(agent): rewrite harness for video editor with Premiere/AE tools"
```

---

### Task 5: Rewrite program.md for video editing

**Files:**
- Modify: `program.md` (full rewrite of editable sections)

**Step 1: Rewrite program.md**

Change the directive from "general coding agent" to "video editor agent." Key changes:

- Directive: Build a professional AI video editor that operates in Premiere Pro and After Effects
- Setup: Note that tasks require Premiere running with MCP bridge active
- Tool strategy: Premiere MCP tools for timeline ops, knowledge tools for technique lookup, AE bridge for motion graphics
- How to run: Host-side execution, not Docker (but still via Harbor for scoring)
- Keep the experiment loop, keep/discard rules, failure analysis, and overfitting rules unchanged — they apply the same way

**Step 2: Commit**

```bash
git add program.md
git commit -m "feat(program): rewrite directive for video editor agent"
```

---

### Task 6: Create Tier 1 benchmark tasks (atomic operations)

**Files:**
- Create: `tasks/tier1-import-clip/task.toml`
- Create: `tasks/tier1-import-clip/instruction.md`
- Create: `tasks/tier1-import-clip/tests/test.sh`
- Create: `tasks/tier1-import-clip/environment/Dockerfile`
- Create: `tasks/tier1-add-title/task.toml`
- Create: `tasks/tier1-add-title/instruction.md`
- Create: `tasks/tier1-add-title/tests/test.sh`
- Create: `tasks/tier1-add-title/environment/Dockerfile`
- Create: `tasks/tier1-cross-dissolve/task.toml`
- Create: `tasks/tier1-cross-dissolve/instruction.md`
- Create: `tasks/tier1-cross-dissolve/tests/test.sh`
- Create: `tasks/tier1-cross-dissolve/environment/Dockerfile`

**Step 1: Create the import-clip task**

`tasks/tier1-import-clip/instruction.md`:
```markdown
Import the file `/test-assets/sample.mp4` into the Premiere Pro project.
Create a new sequence called "Test Sequence" and place the clip on video
track V1 starting at 00:00:00.
```

`tasks/tier1-import-clip/tests/test.sh`:
The verifier calls Premiere MCP to check:
- A sequence named "Test Sequence" exists
- V1 has at least 1 clip
- The clip starts at time 0

Write the verifier as a Python script that uses httpx to call the Premiere MCP inspection tools, then writes score to `/logs/verifier/reward.txt`.

**Step 2: Create the add-title task**

`tasks/tier1-add-title/instruction.md`:
```markdown
In the active Premiere Pro sequence, add a text title that says
"HELLO WORLD" centered on screen. Place it on the timeline starting at
5 seconds with a duration of 3 seconds.
```

Verifier checks: timeline has a text/graphics clip at ~5s with ~3s duration.

**Step 3: Create the cross-dissolve task**

`tasks/tier1-cross-dissolve/instruction.md`:
```markdown
The active Premiere Pro sequence has two clips on V1.
Add a Cross Dissolve transition between clip 1 and clip 2 with a
duration of 1 second.
```

Verifier checks: a transition exists between the two clips.

**Step 4: Each task gets a minimal Dockerfile**

```dockerfile
FROM autoagent-base
```

**Step 5: Each task.toml follows Harbor format**

```toml
[task]
name = "autoagent/tier1-import-clip"
description = "Import a clip and place on timeline"
timeout = 120
```

**Step 6: Commit**

```bash
git add tasks/tier1-*/
git commit -m "feat(tasks): add 3 tier-1 benchmark tasks for atomic Premiere operations"
```

---

### Task 7: Discover Premiere MCP transport and wire up tools

**Files:**
- Modify: `tools/premiere.py` — fill in `_call_premiere_mcp` implementation

**Step 1: Discover how the Premiere MCP bridge is exposed**

With Premiere running and the MCP bridge active, probe for the transport:

```bash
# Check common MCP ports
curl -s http://localhost:3000/ 2>&1
curl -s http://localhost:8080/ 2>&1
# Check if there's an MCP config in the user's Claude settings
cat ~/.claude/settings.json | python -m json.tool 2>&1 | grep -i premiere
# Check for the CEP panel's communication method
ls ~/AppData/Roaming/Adobe/CEP/extensions/ 2>&1
```

**Step 2: Implement `_call_premiere_mcp` based on discovery**

If HTTP: use `httpx` to POST tool calls.
If file-bridge: write `.jsx` commands to the polling directory.
If the MCP is only accessible through Claude Code's MCP infrastructure: create a thin Node.js script that acts as a proxy, or use the `mcp` Python package to connect directly.

**Step 3: Test one tool call**

```bash
uv run python -c "
import asyncio
from tools.premiere import premiere_get_project_info
# Call the tool function directly (unwrap the function_tool decorator)
result = asyncio.run(premiere_get_project_info.invoke(None, '{}'))
print(result)
"
```

Expected: JSON with current project info.

**Step 4: Commit**

```bash
git add tools/premiere.py
git commit -m "feat(tools): wire up Premiere MCP transport"
```

---

### Task 8: Run first benchmark and establish baseline

**Step 1: Ensure Premiere is running with a test project**

Open Premiere Pro, create or open a project with at least one test asset available.

**Step 2: Remove the hello-world test task**

```bash
rm -rf tasks/hello-world
```

**Step 3: Run the tier-1 tasks**

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 rm -rf jobs; mkdir -p jobs && \
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run harbor run -p tasks/ \
  -n 1 --agent-import-path agent:AutoAgent -o jobs --job-name baseline
```

**Step 4: Record baseline in results.tsv**

```bash
echo -e "commit\tavg_score\tpassed\ttask_scores\tcost_usd\tstatus\tdescription" > results.tsv
# Add baseline row after reading results
```

**Step 5: Commit baseline**

```bash
git add results.tsv
git commit -m "feat: establish baseline results for tier-1 tasks"
```

---

### Task 9: Iterate on harness based on baseline results

This is where the AutoAgent meta-loop takes over. Read `program.md` and begin the experiment cycle:

1. Read baseline `run.log` and per-task results
2. Diagnose failures from trajectories
3. Group by root cause (missing tool? bad prompt? wrong parameters?)
4. Choose one improvement
5. Edit harness
6. Rerun
7. Record results
8. Keep or discard

This task is ongoing — the meta-agent runs it autonomously.

**Step 1: Push all work so far**

```bash
git push origin main
```
