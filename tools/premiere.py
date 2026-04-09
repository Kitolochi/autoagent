"""Premiere Pro MCP tools for the video editor agent.

Connects to the Premiere Pro MCP HTTP server via Streamable HTTP transport,
then exposes key tools as @function_tool for the OpenAI Agents SDK.

Prerequisites:
    Start the HTTP server before using these tools:
        node C:/Users/chris/lifeautomation/premiere-pro-mcp/dist/http-server.js
    Default port: 3000 (override with PREMIERE_MCP_URL env var)
"""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import AsyncExitStack

from agents import function_tool
from agents.tool import FunctionTool
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

PREMIERE_MCP_URL = os.environ.get("PREMIERE_MCP_URL", "http://localhost:3001/mcp")

# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------
# The MCP Streamable HTTP client is an async context manager that yields
# (read_stream, write_stream, get_session_id).  We keep it alive for the
# lifetime of the process using an AsyncExitStack managed by a background task.

_session: ClientSession | None = None
_exit_stack: AsyncExitStack | None = None
_lock = asyncio.Lock()


async def _get_session() -> ClientSession:
    """Return (or create) a persistent MCP client session."""
    global _session, _exit_stack
    async with _lock:
        if _session is not None:
            return _session

        _exit_stack = AsyncExitStack()
        read_stream, write_stream, _ = await _exit_stack.enter_async_context(
            streamable_http_client(PREMIERE_MCP_URL)
        )
        _session = await _exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await _session.initialize()
        return _session


async def close_session() -> None:
    """Tear down the MCP session (call on shutdown)."""
    global _session, _exit_stack
    async with _lock:
        if _exit_stack is not None:
            await _exit_stack.aclose()
        _session = None
        _exit_stack = None


async def _call_tool(name: str, arguments: dict) -> str:
    """Call a Premiere MCP tool and return the text result."""
    session = await _get_session()
    try:
        result = await session.call_tool(name, arguments)
    except Exception as exc:
        # Session may have died; reset and retry once
        await close_session()
        session = await _get_session()
        result = await session.call_tool(name, arguments)

    if result.isError:
        texts = [b.text for b in result.content if hasattr(b, "text")]
        return f"ERROR: {' '.join(texts)}"

    texts = [b.text for b in result.content if hasattr(b, "text")]
    return "\n".join(texts) if texts else json.dumps(result.structuredContent or {})


# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------
# Each function exposes one Premiere MCP tool as an @function_tool.
# Parameters use simple types only (str, int, float, bool) so the
# OpenAI Agents SDK can generate JSON schemas for them.


@function_tool
async def get_project_info() -> str:
    """Get information about the currently open Premiere Pro project."""
    return await _call_tool("get_project_info", {})


@function_tool
async def get_active_sequence() -> str:
    """Get information about the active sequence in Premiere Pro."""
    return await _call_tool("get_active_sequence", {})


@function_tool
async def get_timeline_summary() -> str:
    """Get a summary of all tracks and clips on the active timeline."""
    return await _call_tool("get_timeline_summary", {})


@function_tool
async def get_full_sequence_info() -> str:
    """Get complete information about the active sequence including all tracks and clips."""
    return await _call_tool("get_full_sequence_info", {})


@function_tool
async def get_total_clip_count() -> str:
    """Get the total number of clips on the active timeline."""
    return await _call_tool("get_total_clip_count", {})


@function_tool
async def get_clip_properties(track_type: str, track_index: int, clip_index: int) -> str:
    """Get properties of a specific clip.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip on the track.
    """
    return await _call_tool("get_clip_properties", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
    })


@function_tool
async def list_clip_effects(track_type: str, track_index: int, clip_index: int) -> str:
    """List all effects applied to a specific clip.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip on the track.
    """
    return await _call_tool("list_clip_effects", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
    })


@function_tool
async def import_media(file_path: str, bin_path: str = "") -> str:
    """Import a media file into the Premiere Pro project.

    Args:
        file_path: Absolute path to the media file to import.
        bin_path: Optional bin path to import into (e.g. "Footage/B-Roll").
    """
    args: dict = {"filePath": file_path}
    if bin_path:
        args["binPath"] = bin_path
    return await _call_tool("import_media", args)


@function_tool
async def create_sequence(name: str, preset: str = "") -> str:
    """Create a new sequence in the Premiere Pro project.

    Args:
        name: Name for the new sequence.
        preset: Optional preset name for the sequence.
    """
    args: dict = {"name": name}
    if preset:
        args["preset"] = preset
    return await _call_tool("create_sequence", args)


@function_tool
async def add_to_timeline(
    clip_name: str,
    track_index: int = 0,
    position: float = 0.0,
    track_type: str = "video",
) -> str:
    """Add a project item to the timeline.

    Args:
        clip_name: Name of the project item (clip) to add.
        track_index: Zero-based index of the target track.
        position: Position in seconds where the clip should be placed.
        track_type: Type of track, either "video" or "audio".
    """
    return await _call_tool("add_to_timeline", {
        "clipName": clip_name,
        "trackIndex": track_index,
        "position": position,
        "trackType": track_type,
    })


@function_tool
async def add_text_overlay(
    text: str,
    track_index: int = 1,
    start_time: float = 0.0,
    duration: float = 5.0,
) -> str:
    """Add a text overlay (title) to the timeline.

    Args:
        text: The text content to display.
        track_index: Zero-based video track index for the overlay.
        start_time: Start time in seconds.
        duration: Duration in seconds.
    """
    return await _call_tool("add_text_overlay", {
        "text": text,
        "trackIndex": track_index,
        "startTime": start_time,
        "duration": duration,
    })


@function_tool
async def add_transition_to_clip(
    track_index: int,
    clip_index: int,
    transition_name: str = "Cross Dissolve",
    duration: float = 1.0,
    position: str = "start",
) -> str:
    """Add a transition to a clip on the timeline.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        transition_name: Name of the transition effect.
        duration: Transition duration in seconds.
        position: Where to apply: "start", "end", or "both".
    """
    return await _call_tool("add_transition_to_clip", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "transitionName": transition_name,
        "duration": duration,
        "position": position,
    })


@function_tool
async def apply_effect(
    track_type: str,
    track_index: int,
    clip_index: int,
    effect_name: str,
) -> str:
    """Apply a video or audio effect to a clip.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based track index.
        clip_index: Zero-based clip index on the track.
        effect_name: Name of the effect to apply (e.g. "Gaussian Blur").
    """
    return await _call_tool("apply_effect", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "effectName": effect_name,
    })


@function_tool
async def adjust_audio_levels(
    track_index: int,
    clip_index: int,
    level_db: float,
) -> str:
    """Adjust the audio level of a clip.

    Args:
        track_index: Zero-based audio track index.
        clip_index: Zero-based clip index on the track.
        level_db: Audio level in decibels (0.0 is unity, negative values reduce volume).
    """
    return await _call_tool("adjust_audio_levels", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "levelDb": level_db,
    })


@function_tool
async def color_correct(
    track_index: int,
    clip_index: int,
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float = 100.0,
    temperature: float = 0.0,
) -> str:
    """Apply color correction to a video clip.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        brightness: Brightness adjustment value.
        contrast: Contrast adjustment value.
        saturation: Saturation percentage (100.0 is normal).
        temperature: Color temperature adjustment value.
    """
    return await _call_tool("color_correct", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "temperature": temperature,
    })


@function_tool
async def add_marker(
    time: float,
    name: str = "",
    color: str = "green",
    comment: str = "",
) -> str:
    """Add a marker to the active sequence.

    Args:
        time: Position in seconds for the marker.
        name: Optional name for the marker.
        color: Marker color (green, red, blue, yellow, orange, purple, white).
        comment: Optional comment text for the marker.
    """
    args: dict = {"time": time, "color": color}
    if name:
        args["name"] = name
    if comment:
        args["comment"] = comment
    return await _call_tool("add_marker", args)


@function_tool
async def trim_clip(
    track_type: str,
    track_index: int,
    clip_index: int,
    trim_start: float = 0.0,
    trim_end: float = 0.0,
) -> str:
    """Trim a clip's in or out point.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based track index.
        clip_index: Zero-based clip index on the track.
        trim_start: Seconds to trim from the start (positive trims inward).
        trim_end: Seconds to trim from the end (positive trims inward).
    """
    return await _call_tool("trim_clip", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "trimStart": trim_start,
        "trimEnd": trim_end,
    })


@function_tool
async def move_clip(
    track_type: str,
    track_index: int,
    clip_index: int,
    new_position: float,
    new_track_index: int = -1,
) -> str:
    """Move a clip to a new position or track.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based track index of the source clip.
        clip_index: Zero-based clip index on the source track.
        new_position: New position in seconds.
        new_track_index: Target track index (-1 to keep on same track).
    """
    args: dict = {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "newPosition": new_position,
    }
    if new_track_index >= 0:
        args["newTrackIndex"] = new_track_index
    return await _call_tool("move_clip", args)


@function_tool
async def set_playhead_position(time: float) -> str:
    """Move the playhead to a specific time position.

    Args:
        time: Position in seconds.
    """
    return await _call_tool("set_playhead_position", {"time": time})


@function_tool
async def get_playhead_position() -> str:
    """Get the current playhead position in the active sequence."""
    return await _call_tool("get_playhead_position", {})


@function_tool
async def save_project() -> str:
    """Save the current Premiere Pro project."""
    return await _call_tool("save_project", {})


@function_tool
async def export_sequence(
    output_path: str,
    preset_name: str = "H.264 - Match Source - High Bitrate",
) -> str:
    """Export the active sequence using Adobe Media Encoder.

    Args:
        output_path: Absolute file path for the exported file.
        preset_name: AME preset name to use for encoding.
    """
    return await _call_tool("export_sequence", {
        "outputPath": output_path,
        "presetName": preset_name,
    })


@function_tool
async def split_clip(
    track_type: str,
    track_index: int,
    clip_index: int,
    split_time: float,
) -> str:
    """Split a clip at a specific time.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based track index.
        clip_index: Zero-based clip index on the track.
        split_time: Time in seconds at which to split the clip.
    """
    return await _call_tool("split_clip", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "splitTime": split_time,
    })


@function_tool
async def remove_from_timeline(
    track_type: str,
    track_index: int,
    clip_index: int,
) -> str:
    """Remove a clip from the timeline.

    Args:
        track_type: Type of track, either "video" or "audio".
        track_index: Zero-based track index.
        clip_index: Zero-based clip index on the track.
    """
    return await _call_tool("remove_from_timeline", {
        "trackType": track_type,
        "trackIndex": track_index,
        "clipIndex": clip_index,
    })


@function_tool
async def speed_change(
    track_index: int,
    clip_index: int,
    speed: float,
) -> str:
    """Change the playback speed of a clip.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        speed: Speed multiplier (1.0 is normal, 2.0 is double speed, 0.5 is half speed).
    """
    return await _call_tool("speed_change", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "speed": speed,
    })


@function_tool
async def set_clip_opacity(
    track_index: int,
    clip_index: int,
    opacity: float,
) -> str:
    """Set the opacity of a video clip.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        opacity: Opacity percentage (0.0 to 100.0).
    """
    return await _call_tool("set_clip_opacity", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "opacity": opacity,
    })


@function_tool
async def set_clip_volume(
    track_index: int,
    clip_index: int,
    volume: float,
) -> str:
    """Set the volume of an audio clip.

    Args:
        track_index: Zero-based audio track index.
        clip_index: Zero-based clip index on the track.
        volume: Volume level (0.0 to 1.0, where 1.0 is unity gain).
    """
    return await _call_tool("set_clip_volume", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "volume": volume,
    })


@function_tool
async def list_sequences() -> str:
    """List all sequences in the current Premiere Pro project."""
    return await _call_tool("list_sequences", {})


@function_tool
async def set_active_sequence(sequence_name: str) -> str:
    """Set a sequence as the active sequence by name.

    Args:
        sequence_name: Name of the sequence to activate.
    """
    return await _call_tool("set_active_sequence", {"sequenceName": sequence_name})


@function_tool
async def list_project_items(bin_path: str = "") -> str:
    """List project items (media, sequences, bins) in the project panel.

    Args:
        bin_path: Optional bin path to list contents of (empty for root).
    """
    args: dict = {}
    if bin_path:
        args["binPath"] = bin_path
    return await _call_tool("list_project_items", args)


@function_tool
async def undo() -> str:
    """Undo the last action in Premiere Pro."""
    return await _call_tool("undo", {})


@function_tool
async def redo() -> str:
    """Redo the last undone action in Premiere Pro."""
    return await _call_tool("redo", {})


# ---------------------------------------------------------------------------
# New high-priority tools for social media editing
# ---------------------------------------------------------------------------

@function_tool
async def add_audio_keyframes(
    track_index: int,
    clip_index: int,
    keyframes: str,
) -> str:
    """Add volume keyframes to an audio clip for ducking/automation.

    Args:
        track_index: Zero-based audio track index.
        clip_index: Zero-based clip index on the track.
        keyframes: JSON string of list[{timeSeconds, levelDb}].
    """
    import json
    kf_list = json.loads(keyframes)
    return await _call_tool("add_audio_keyframes", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "keyframes": kf_list,
    })


@function_tool
async def apply_lut(
    track_index: int,
    clip_index: int,
    lut_path: str,
) -> str:
    """Apply a LUT (Look-Up Table) to a video clip for color grading.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        lut_path: Absolute path to .cube or .look LUT file.
    """
    return await _call_tool("apply_lut", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "lutPath": lut_path,
    })


@function_tool
async def import_mogrt(file_path: str, bin_path: str = "") -> str:
    """Import a Motion Graphics Template (.mogrt) into the project.

    Args:
        file_path: Absolute path to the .mogrt file.
        bin_path: Optional bin path to import into.
    """
    args: dict = {"filePath": file_path}
    if bin_path:
        args["binPath"] = bin_path
    return await _call_tool("import_mogrt", args)


@function_tool
async def add_keyframe(
    track_index: int,
    clip_index: int,
    property_name: str,
    time_seconds: float,
    value: str,
) -> str:
    """Add a keyframe for transform properties (position, scale, rotation).

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        property_name: Property name - "position", "scale", "rotation", "anchor_point", or "opacity".
        time_seconds: Time in seconds from clip start.
        value: JSON string - "[x, y]" for position/anchor, "1.5" for scale/rotation/opacity.
    """
    import json
    val = json.loads(value)
    return await _call_tool("add_keyframe", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "propertyName": property_name,
        "timeSeconds": time_seconds,
        "value": val,
    })


@function_tool
async def reverse_clip(track_index: int, clip_index: int) -> str:
    """Reverse a clip (plays backwards) for dramatic reveals.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
    """
    return await _call_tool("reverse_clip", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
    })


@function_tool
async def batch_apply_effect(
    effect_name: str,
    clips: str,
) -> str:
    """Apply the same effect to multiple clips at once.

    Args:
        effect_name: Name of the effect to apply (e.g., "Gaussian Blur").
        clips: JSON string of list[{trackIndex, clipIndex}] identifying clips.
    """
    import json
    clips_list = json.loads(clips)
    return await _call_tool("batch_apply_effect", {
        "effectName": effect_name,
        "clips": clips_list,
    })


@function_tool
async def set_blend_mode(
    track_index: int,
    clip_index: int,
    blend_mode: str,
) -> str:
    """Set the blend mode for compositing overlays.

    Args:
        track_index: Zero-based video track index.
        clip_index: Zero-based clip index on the track.
        blend_mode: Blend mode name - "Normal", "Multiply", "Screen", "Overlay", "Add", etc.
    """
    return await _call_tool("set_blend_mode", {
        "trackIndex": track_index,
        "clipIndex": clip_index,
        "blendMode": blend_mode,
    })


@function_tool
async def nest_clips(
    clips: str,
    sequence_name: str,
) -> str:
    """Nest selected clips into a new sequence for organization.

    Args:
        clips: JSON string of list[{trackIndex, clipIndex}] identifying clips to nest.
        sequence_name: Name for the new nested sequence.
    """
    import json
    clips_list = json.loads(clips)
    return await _call_tool("nest_clips", {
        "clips": clips_list,
        "sequenceName": sequence_name,
    })


# ---------------------------------------------------------------------------
# Tool collection
# ---------------------------------------------------------------------------

def get_all_premiere_tools() -> list[FunctionTool]:
    """Return all Premiere Pro tools for use with the OpenAI Agents SDK."""
    return [
        get_project_info,
        get_active_sequence,
        get_timeline_summary,
        get_full_sequence_info,
        get_total_clip_count,
        get_clip_properties,
        list_clip_effects,
        import_media,
        create_sequence,
        add_to_timeline,
        add_text_overlay,
        add_transition_to_clip,
        apply_effect,
        adjust_audio_levels,
        color_correct,
        add_marker,
        trim_clip,
        move_clip,
        set_playhead_position,
        get_playhead_position,
        save_project,
        export_sequence,
        split_clip,
        remove_from_timeline,
        speed_change,
        set_clip_opacity,
        set_clip_volume,
        list_sequences,
        set_active_sequence,
        list_project_items,
        undo,
        redo,
        # High-priority social media editing tools
        add_audio_keyframes,
        apply_lut,
        import_mogrt,
        add_keyframe,
        reverse_clip,
        batch_apply_effect,
        set_blend_mode,
        nest_clips,
    ]
