"""Single-file Harbor agent harness: --agent-import-path agent:AutoAgent."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from agents import Agent, Runner, function_tool
from agents.items import (
    ItemHelpers,
    MessageOutputItem,
    ReasoningItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.tool import FunctionTool
from agents.usage import Usage
from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from openai import AsyncOpenAI


# ============================================================================
# EDITABLE HARNESS — prompt, tools, agent construction
# ============================================================================

from pathlib import Path
from tools.premiere import get_all_premiere_tools
from tools.knowledge import get_all_knowledge_tools

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def _load_knowledge(filename: str) -> str:
    path = KNOWLEDGE_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


TECHNIQUE_REF = _load_knowledge("techniques.md")
AE_GOTCHAS = _load_knowledge("ae-gotchas.md")

SYSTEM_PROMPT = f"""You are a professional video editor working in Adobe Premiere Pro and After Effects.

## Your Workflow
1. PLAN — Break down the task into discrete, verifiable steps using create_edit_plan.
2. INSPECT — Check the current project and timeline state before making changes.
3. EXECUTE — Make the edits step-by-step, following your plan.
4. VERIFY — After completing all steps, use verify_timeline to confirm requirements are met.

## Planning Requirements
For ANY task with more than one operation, you MUST:
- Call create_edit_plan FIRST with the task description
- Reference the plan steps as you execute
- Mark steps complete as you go
- Call verify_timeline BEFORE reporting success

## Execution Rules
- Always call get_active_sequence or get_timeline_summary before editing.
- After each major edit, inspect the timeline to confirm the change.
- Use transitions between clips unless the task specifies hard cuts.
- For text, use add_text_overlay for simple titles.
- For complex motion graphics, use After Effects via run_shell with ExtendScript.
- When applying effects, check list_clip_effects after to confirm.

## Error Recovery
If a tool returns ERROR:
1. Read the error message carefully
2. Check your parameters match the tool's requirements
3. Inspect current state with get_timeline_summary or get_full_sequence_info
4. Adjust parameters and retry ONCE
5. If second attempt fails, try an alternative approach or call undo

## Video Technique Reference
{TECHNIQUE_REF}

## After Effects Gotchas
{AE_GOTCHAS}
"""

MODEL = os.getenv("AUTOAGENT_MODEL", "claude-sonnet-4-6")
MAX_TURNS = 30

PROXY_BASE_URL = os.getenv("AUTOAGENT_PROXY_URL", "http://127.0.0.1:8741/claude/v1")
_client = AsyncOpenAI(base_url=PROXY_BASE_URL, api_key="not-needed")
_model = OpenAIChatCompletionsModel(model=MODEL, openai_client=_client)


def create_tools(environment: BaseEnvironment) -> list[FunctionTool]:
    """Create tools for the agent — Premiere, knowledge, planning, verification, and shell."""

    # Shared state for plan tracking across tool calls
    _plan_state = {"steps": [], "completed": []}

    @function_tool
    async def create_edit_plan(task_description: str) -> str:
        """Create a structured plan for a video editing task.

        Breaks down the task into numbered steps with clear success criteria.
        Returns a formatted plan that can be referenced during execution.

        Args:
            task_description: The full task instruction to break down
        """
        # Parse the task and create structured steps
        lines = task_description.strip().split("\n")
        steps = []
        step_num = 1

        # Extract explicit steps if present
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # Remove numbering/bullets
                cleaned = line.lstrip("0123456789.-•) ").strip()
                if cleaned:
                    steps.append(f"{step_num}. {cleaned}")
                    step_num += 1

        # If no explicit steps found, create basic workflow steps
        if not steps:
            if "sequence" in task_description.lower() and "create" in task_description.lower():
                steps.append("1. Create new sequence with specified name")
                step_num = 2
            if "clip" in task_description.lower() or "media" in task_description.lower():
                steps.append(f"{step_num}. Import or create media items")
                step_num += 1
                steps.append(f"{step_num}. Add clips to timeline at specified positions")
                step_num += 1
            if "text" in task_description.lower() or "title" in task_description.lower():
                steps.append(f"{step_num}. Add text overlays with specified content and timing")
                step_num += 1
            if "transition" in task_description.lower():
                steps.append(f"{step_num}. Apply transitions between clips")
                step_num += 1
            if "effect" in task_description.lower() or "color" in task_description.lower():
                steps.append(f"{step_num}. Apply effects or color corrections")
                step_num += 1
            steps.append(f"{step_num}. Verify timeline state matches requirements")

        _plan_state["steps"] = steps
        _plan_state["completed"] = []

        plan_text = "EDIT PLAN:\n" + "\n".join(steps)
        plan_text += "\n\nExecute these steps in order. After each step, verify it succeeded before proceeding."
        return plan_text

    @function_tool
    async def verify_timeline(requirements: str) -> str:
        """Verify the current timeline state matches task requirements.

        Inspects the timeline and checks if all requirements are met.
        Returns structured feedback on what's correct and what's missing.

        Args:
            requirements: Description of what should be present on the timeline
        """
        from tools.premiere import _call_tool

        # Gather timeline state
        try:
            timeline_info = await _call_tool("get_full_sequence_info", {})
            summary = await _call_tool("get_timeline_summary", {})
        except Exception as e:
            return f"ERROR: Could not inspect timeline: {e}"

        # Build verification report
        report = ["VERIFICATION REPORT:", ""]
        report.append("Current Timeline State:")
        report.append(summary[:500])  # Truncate to keep response manageable
        report.append("")

        # Check against requirements
        requirements_lower = requirements.lower()
        checks = []

        # Check for sequence existence
        if "sequence" in requirements_lower:
            if "active sequence" in summary.lower() or "sequence:" in summary.lower():
                checks.append("✓ Sequence exists")
            else:
                checks.append("✗ No active sequence found")

        # Check for clips
        if "clip" in requirements_lower or "bars and tone" in requirements_lower:
            if "track 0" in summary.lower() or "video track" in summary.lower():
                checks.append("✓ Clips found on timeline")
            else:
                checks.append("✗ No clips found on timeline")

        # Check for text overlays
        if "text" in requirements_lower or "title" in requirements_lower or "overlay" in requirements_lower:
            if "text" in summary.lower() or "title" in summary.lower() or "track 1" in summary.lower() or "track 2" in summary.lower():
                checks.append("✓ Text overlay likely present")
            else:
                checks.append("✗ No text overlay found")

        # Check for transitions
        if "transition" in requirements_lower:
            if "transition" in timeline_info.lower() or "dissolve" in timeline_info.lower():
                checks.append("✓ Transition found")
            else:
                checks.append("✗ No transition found (check get_full_sequence_info for transition details)")

        # Check for markers
        if "marker" in requirements_lower:
            if "marker" in summary.lower() or "marker" in timeline_info.lower():
                checks.append("✓ Markers found")
            else:
                checks.append("✗ No markers found")

        report.append("Requirement Checks:")
        report.extend(checks)
        report.append("")

        # Determine overall status
        failed_checks = [c for c in checks if c.startswith("✗")]
        if failed_checks:
            report.append(f"STATUS: INCOMPLETE ({len(failed_checks)} requirements not met)")
            report.append("NEXT STEPS:")
            for check in failed_checks:
                report.append(f"  - Address: {check[2:]}")  # Remove the ✗ symbol
        else:
            report.append("STATUS: COMPLETE (all detectable requirements met)")

        return "\n".join(report)

    @function_tool
    async def run_shell(command: str) -> str:
        """Run a shell command on the host. Returns stdout and stderr."""
        try:
            result = await environment.exec(command=command, timeout_sec=120)
            out = ""
            if result.stdout:
                out += result.stdout
            if result.stderr:
                out += f"\nSTDERR:\n{result.stderr}" if out else f"STDERR:\n{result.stderr}"
            return out or "(no output)"
        except Exception as exc:
            return f"ERROR: {exc}"

    return [create_edit_plan, verify_timeline, run_shell] + get_all_premiere_tools() + get_all_knowledge_tools()


def create_agent(environment: BaseEnvironment) -> Agent:
    """Build the video editor agent with Premiere, AE, and knowledge tools."""
    tools = create_tools(environment)
    return Agent(
        name="autoagent",
        instructions=SYSTEM_PROMPT,
        tools=tools,
        model=_model,
    )


async def run_task(
    environment: BaseEnvironment,
    instruction: str,
) -> tuple[object, int]:
    """Run the agent on a task and return (result, duration_ms)."""
    agent = create_agent(environment)
    t0 = time.time()
    result = await Runner.run(agent, input=instruction, max_turns=MAX_TURNS)
    duration_ms = int((time.time() - t0) * 1000)
    return result, duration_ms


# ============================================================================
# FIXED ADAPTER BOUNDARY: do not modify unless the human explicitly asks.
# Harbor integration and trajectory serialization live here.
# ============================================================================

def to_atif(result: object, model: str, duration_ms: int = 0) -> dict:
    """Convert OpenAI Agents SDK RunResult to an ATIF trajectory dict."""
    steps: list[dict] = []
    step_id = 0
    now = datetime.now(timezone.utc).isoformat()

    def _step(source: str, message: str, **extra: object) -> dict:
        nonlocal step_id
        step_id += 1
        step = {
            "step_id": step_id,
            "timestamp": now,
            "source": source,
            "message": message,
        }
        step.update({key: value for key, value in extra.items() if value is not None})
        return step

    pending_tool_call = None
    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            if text:
                steps.append(_step("agent", text, model_name=model))
        elif isinstance(item, ReasoningItem):
            summaries = getattr(item.raw_item, "summary", None)
            reasoning = "\n".join(s.text for s in summaries if hasattr(s, "text")) if summaries else None
            if reasoning:
                steps.append(
                    _step(
                        "agent",
                        "(thinking)",
                        reasoning_content=reasoning,
                        model_name=model,
                    )
                )
        elif isinstance(item, ToolCallItem):
            raw = item.raw_item
            if hasattr(raw, "name"):
                pending_tool_call = raw
        elif isinstance(item, ToolCallOutputItem) and pending_tool_call:
            arguments = (
                json.loads(pending_tool_call.arguments)
                if isinstance(pending_tool_call.arguments, str)
                else pending_tool_call.arguments
            )
            output_str = str(item.output) if item.output else ""
            steps.append(
                _step(
                    "agent",
                    f"Tool: {pending_tool_call.name}",
                    tool_calls=[
                        {
                            "tool_call_id": pending_tool_call.call_id,
                            "function_name": pending_tool_call.name,
                            "arguments": arguments,
                        }
                    ],
                    observation={
                        "results": [
                            {
                                "source_call_id": pending_tool_call.call_id,
                                "content": output_str,
                            }
                        ]
                    },
                )
            )
            pending_tool_call = None

    if pending_tool_call:
        arguments = (
            json.loads(pending_tool_call.arguments)
            if isinstance(pending_tool_call.arguments, str)
            else pending_tool_call.arguments
        )
        steps.append(
            _step(
                "agent",
                f"Tool: {pending_tool_call.name}",
                tool_calls=[
                    {
                        "tool_call_id": pending_tool_call.call_id,
                        "function_name": pending_tool_call.name,
                        "arguments": arguments,
                    }
                ],
            )
        )

    if not steps:
        steps.append(_step("user", "(empty)"))

    usage = Usage()
    for response in result.raw_responses:
        usage.add(response.usage)

    return {
        "schema_version": "ATIF-v1.6",
        "session_id": getattr(result, "last_response_id", None) or "unknown",
        "agent": {"name": "autoagent", "version": "0.1.0", "model_name": model},
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": usage.input_tokens,
            "total_completion_tokens": usage.output_tokens,
            "total_cached_tokens": getattr(usage.input_tokens_details, "cached_tokens", 0) or 0,
            "total_cost_usd": None,
            "total_steps": len(steps),
            "extra": {"duration_ms": duration_ms, "num_turns": len(result.raw_responses)},
        },
    }


class AutoAgent(BaseAgent):
    """Harbor agent adapter. Runs the OpenAI agent host-side and proxies shell into the container."""

    SUPPORTS_ATIF = True

    def __init__(self, *args, extra_env: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._extra_env = dict(extra_env) if extra_env else {}

    @staticmethod
    def name() -> str:
        return "autoagent"

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        pass

    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        await environment.exec(command="mkdir -p /task")
        # Ensure instruction.md's parent directory exists
        instr_file = self.logs_dir / "instruction.md"
        instr_file.parent.mkdir(parents=True, exist_ok=True)
        instr_file.write_text(instruction)
        await environment.upload_file(source_path=instr_file, target_path="/task/instruction.md")

        result, duration_ms = await run_task(environment, instruction)

        atif = to_atif(result, model=MODEL, duration_ms=duration_ms)
        traj_path = self.logs_dir / "agent" / "trajectory.json"
        traj_path.parent.mkdir(parents=True, exist_ok=True)
        traj_path.write_text(json.dumps(atif, indent=2))

        try:
            final_metrics = atif.get("final_metrics", {})
            context.n_input_tokens = final_metrics.get("total_prompt_tokens", 0)
            context.n_output_tokens = final_metrics.get("total_completion_tokens", 0)
            context.n_cache_tokens = final_metrics.get("total_cached_tokens", 0)
        except Exception:
            pass

        usage = Usage()
        for response in result.raw_responses:
            usage.add(response.usage)
        print(
            f"turns={len(result.raw_responses)} duration_ms={duration_ms} "
            f"input={usage.input_tokens} output={usage.output_tokens}"
        )


__all__ = ["AutoAgent"]
