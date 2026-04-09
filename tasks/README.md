# Video Editor Agent Benchmark Tasks

## Overview

This directory contains Harbor benchmark tasks for the video editor agent, organized into three tiers of increasing complexity.

## Benchmark Tiers

### Tier 1: Atomic Operations ✅
**Status**: 4/4 passing  
**Complexity**: 1-3 tool calls per task  
**Purpose**: Test individual MCP tool functionality

Tasks:
- `tier1-create-sequence` - Create a named sequence
- `tier1-add-clip` - Add a project item to timeline
- `tier1-add-title` - Add text overlay to sequence
- `tier1-add-transition` - Apply transition to clip
- `tier1-adjust-audio` - Adjust clip audio levels
- `tier1-import-media` - Import media file to project

**Test File**: `simple_test_v2.py` (passing with direct API loop)

### Tier 2: Multi-Step Workflows ⚠️
**Status**: 3 tasks created, blocked by MCP timeout  
**Complexity**: 4-6 tool calls per task  
**Purpose**: Test agent's ability to sequence operations

Tasks:
- `tier2-basic-edit` - Sequence + clip + text + transition
- `tier2-titled-sequence` - Sequence with title cards
- `tier2-transition-between-clips` - Two clips with transition

**Test File**: `tier2_test.py` (created, not fully passing due to MCP issues)

### Tier 3: Complex Production Workflows 🆕
**Status**: 5 tasks designed, not yet implemented  
**Complexity**: 8-15+ tool calls per task  
**Purpose**: Test agent's ability to compose complete professional edits

Tasks:
1. **tier3-multi-scene-story** - Narrative with 3 scenes, titles, markers
2. **tier3-color-graded-montage** - 4 clips with color/speed/effects
3. **tier3-podcast-edit** - Audio-centric with lower thirds and B-roll
4. **tier3-social-cutdown** - Vertical format with rapid cuts and captions
5. **tier3-trailer-assembly** - 4-act dramatic structure with audio design

**Test File**: `tier3_test.py` (to be created)

## Task Format

Each task directory contains:
- `instruction.md` - Natural language task description with steps and verification criteria

Tasks are designed to be read by the agent as instructions, with verification logic implemented in the test harness.

## Documentation

- **TIER3-DESIGN.md** - Design philosophy and progression from tier-1 to tier-3
- **TIER3-INDEX.md** - Quick reference for all tier-3 tasks with stats
- **README.md** - This file

## Testing Strategy

**Tier-1**: Direct tool success/failure
- Verification: Did the tool call succeed without error?
- MAX_TURNS: 10

**Tier-2**: Multi-tool workflow completion
- Verification: Were all required tools called successfully?
- MAX_TURNS: 20

**Tier-3**: Structural and compositional correctness
- Verification: Does the output match professional editing standards?
- MAX_TURNS: 30-40 (recommended)
- Deep verification via `get_full_sequence_info`, `get_timeline_summary`

## Implementation Status

```
Tier 1: ████████████████████ 4/4 tests passing
Tier 2: ████░░░░░░░░░░░░░░░░ 3 tasks created, MCP timeout blocking
Tier 3: ░░░░░░░░░░░░░░░░░░░░ 5 tasks designed, tests not yet written
```

## Next Steps

1. Resolve tier-2 MCP timeout issues (may require streaming or batching)
2. Implement `tier3_test.py` with deep verification logic
3. Run tier-3 benchmarks to establish baseline agent capability
4. Iterate on agent prompting and tool usage patterns based on results

## Related Files

- Test harness: `simple_test_v2.py`, `tier2_test.py`
- Premiere tools: `tools/premiere.py`
- Agent configuration: `program/video_editor_directive.md`
