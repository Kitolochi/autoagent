"""Knowledge base lookup tools for the video editor agent."""
from __future__ import annotations
from pathlib import Path
from agents import function_tool

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

@function_tool
async def lookup_technique(query: str) -> str:
    """Search the video technique knowledge base for a technique by name or use case.
    Returns matching technique descriptions from the catalog."""
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
    Returns relevant patterns, workarounds, and known issues."""
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
