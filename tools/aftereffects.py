"""After Effects MCP tools for the video editor agent.

Connects to the After Effects MCP HTTP server via HTTP transport,
then exposes key tools as @function_tool for the OpenAI Agents SDK.

Prerequisites:
    Start the HTTP server before using these tools:
        node C:/Users/chris/lifeautomation/after-effects-mcp/http-server.js
    Default port: 3002 (override with AE_MCP_URL env var)
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from agents import function_tool
from agents.tool import FunctionTool
import httpx

AE_MCP_URL = os.environ.get("AE_MCP_URL", "http://localhost:3002/mcp")

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    """Return (or create) a persistent HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


async def close_client() -> None:
    """Close the HTTP client."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def _call_tool(name: str, arguments: dict[str, Any]) -> str:
    """Call an After Effects MCP tool and return the text result."""
    client = await _get_client()
    try:
        response = await client.post(
            AE_MCP_URL,
            json={"tool": name, "arguments": arguments},
        )
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            return f"ERROR: {result['error']}"

        # Extract content from MCP response format
        if isinstance(result, dict):
            if "content" in result:
                return json.dumps(result["content"])
            return json.dumps(result)
        return str(result)
    except Exception as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------

@function_tool
async def create_ae_composition(
    name: str,
    width: int = 1920,
    height: int = 1080,
    frame_rate: float = 30.0,
    duration: float = 10.0,
    background_color: str = "[0, 0, 0, 1]",
) -> str:
    """Create a new After Effects composition.

    Args:
        name: Composition name.
        width: Width in pixels (default: 1920).
        height: Height in pixels (default: 1080).
        frame_rate: Frame rate (default: 30.0).
        duration: Duration in seconds (default: 10.0).
        background_color: Background color as JSON array [r, g, b, a] (0-1 range).
    """
    import json as _json
    bg_color = _json.loads(background_color)
    return await _call_tool("create-composition", {
        "name": name,
        "width": width,
        "height": height,
        "frameRate": frame_rate,
        "duration": duration,
        "backgroundColor": bg_color,
    })


@function_tool
async def run_ae_script(script: str, timeout_ms: int = 30000) -> str:
    """Run a JSX script inside After Effects.

    Use this for operations not covered by specific tools. The script runs
    in After Effects' ExtendScript engine (JSX/ES3 syntax).

    Args:
        script: JSX/ExtendScript code to execute.
        timeout_ms: Execution timeout in milliseconds (default: 30000).
    """
    return await _call_tool("run-script", {
        "script": script,
        "timeout": timeout_ms,
    })


@function_tool
async def get_ae_results() -> str:
    """Get results from the last script execution in After Effects."""
    return await _call_tool("get-results", {})


@function_tool
async def set_ae_layer_keyframe(
    layer_name: str,
    property_name: str,
    time: float,
    value: str,
) -> str:
    """Add a keyframe to an After Effects layer property.

    Args:
        layer_name: Name of the layer.
        property_name: Property name (e.g., "Position", "Scale", "Rotation", "Opacity").
        time: Time in seconds.
        value: JSON string - "[x, y]" for position, "[100, 100]" for scale, "45" for rotation, etc.
    """
    import json as _json
    val = _json.loads(value)
    return await _call_tool("setLayerKeyframe", {
        "layerName": layer_name,
        "propertyName": property_name,
        "time": time,
        "value": val,
    })


@function_tool
async def set_ae_layer_expression(
    layer_name: str,
    property_name: str,
    expression: str,
) -> str:
    """Add or remove an expression on an After Effects layer property.

    Args:
        layer_name: Name of the layer.
        property_name: Property name (e.g., "Position", "Rotation").
        expression: Expression code (empty string to remove expression).
    """
    return await _call_tool("setLayerExpression", {
        "layerName": layer_name,
        "propertyName": property_name,
        "expression": expression,
    })


@function_tool
async def create_ae_text_layer(
    comp_name: str,
    text: str,
    font_name: str = "Arial",
    font_size: int = 72,
    color: str = "[1, 1, 1, 1]",
    position: str = "[960, 540]",
) -> str:
    """Create a text layer in an After Effects composition.

    Args:
        comp_name: Name of the composition.
        text: Text content.
        font_name: Font name (default: "Arial").
        font_size: Font size in points (default: 72).
        color: Text color as JSON array [r, g, b, a] (0-1 range).
        position: Position as JSON array [x, y].
    """
    import json as _json
    col = _json.loads(color)
    pos = _json.loads(position)

    script = f"""
var comp = app.project.items.findByName("{comp_name}");
if (!comp) throw "Composition not found: {comp_name}";

var textLayer = comp.layers.addText("{text}");
var textProp = textLayer.property("Source Text");
var textDocument = textProp.value;

textDocument.font = "{font_name}";
textDocument.fontSize = {font_size};
textDocument.fillColor = {_json.dumps(col)};

textProp.setValue(textDocument);
textLayer.property("Position").setValue({_json.dumps(pos)});

"Text layer created: " + textLayer.name;
"""
    return await run_ae_script(script)


@function_tool
async def create_ae_shape_layer(
    comp_name: str,
    shape_type: str,
    fill_color: str = "[1, 0, 0, 1]",
    stroke_color: str = "[0, 0, 0, 1]",
    stroke_width: int = 5,
    size: str = "[200, 200]",
    position: str = "[960, 540]",
) -> str:
    """Create a shape layer in an After Effects composition.

    Args:
        comp_name: Name of the composition.
        shape_type: Shape type - "rectangle", "ellipse", "polygon", or "star".
        fill_color: Fill color as JSON array [r, g, b, a] (0-1 range).
        stroke_color: Stroke color as JSON array [r, g, b, a] (0-1 range).
        stroke_width: Stroke width in pixels.
        size: Size as JSON array [width, height].
        position: Position as JSON array [x, y].
    """
    import json as _json
    fill = _json.loads(fill_color)
    stroke = _json.loads(stroke_color)
    sz = _json.loads(size)
    pos = _json.loads(position)

    script = f"""
var comp = app.project.items.findByName("{comp_name}");
if (!comp) throw "Composition not found: {comp_name}";

var shapeLayer = comp.layers.addShape();
var shapeGroup = shapeLayer.property("Contents").addProperty("ADBE Vector Group");

// Add shape
var shape;
switch("{shape_type}") {{
    case "rectangle":
        shape = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Rect");
        shape.property("Size").setValue({_json.dumps(sz)});
        break;
    case "ellipse":
        shape = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Ellipse");
        shape.property("Size").setValue({_json.dumps(sz)});
        break;
    default:
        shape = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Rect");
        shape.property("Size").setValue({_json.dumps(sz)});
}}

// Add fill
var fill = shapeGroup.property("Contents").addProperty("ADBE Vector Graphic - Fill");
fill.property("Color").setValue({_json.dumps(fill)});

// Add stroke
var stroke = shapeGroup.property("Contents").addProperty("ADBE Vector Graphic - Stroke");
stroke.property("Color").setValue({_json.dumps(stroke)});
stroke.property("Stroke Width").setValue({stroke_width});

shapeLayer.property("Position").setValue({_json.dumps(pos)});

"Shape layer created: " + shapeLayer.name;
"""
    return await run_ae_script(script)


@function_tool
async def render_ae_comp(
    comp_name: str,
    output_path: str,
    format: str = "H.264",
) -> str:
    """Render an After Effects composition to a file.

    Args:
        comp_name: Name of the composition to render.
        output_path: Absolute path for output file (include extension).
        format: Render format - "H.264" (mp4), "QuickTime", or "PNG Sequence".
    """
    script = f"""
var comp = app.project.items.findByName("{comp_name}");
if (!comp) throw "Composition not found: {comp_name}";

var queue = app.project.renderQueue;
var item = queue.items.add(comp);
var outputModule = item.outputModule(1);

// Set format
switch("{format}") {{
    case "H.264":
        outputModule.applyTemplate("H.264");
        break;
    case "QuickTime":
        outputModule.applyTemplate("Best Settings");
        break;
    case "PNG Sequence":
        outputModule.applyTemplate("PNG Sequence");
        break;
}}

outputModule.file = new File("{output_path.replace('\\', '\\\\')}");

// Start render
queue.render();

"Render started: " + "{output_path}";
"""
    return await run_ae_script(script)


# ---------------------------------------------------------------------------
# Tool collection
# ---------------------------------------------------------------------------

def get_all_ae_tools() -> list[FunctionTool]:
    """Return all After Effects tools for use with the OpenAI Agents SDK."""
    return [
        create_ae_composition,
        run_ae_script,
        get_ae_results,
        set_ae_layer_keyframe,
        set_ae_layer_expression,
        create_ae_text_layer,
        create_ae_shape_layer,
        render_ae_comp,
    ]
