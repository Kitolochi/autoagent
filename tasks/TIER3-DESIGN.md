# Tier-3 Benchmark Design Philosophy

## Overview

Tier-3 benchmarks test the video editor agent's ability to plan and execute complete, realistic video editing workflows that require compositional thinking, multi-step coordination, and professional editing judgement.

## Progression from Tier-1 and Tier-2

**Tier-1: Atomic Operations** (4 tasks, all passing)
- Single tool call or simple 2-3 step sequences
- Test individual MCP tool functionality
- Verification: Did the tool succeed?
- Examples: Create sequence, add text, add transition, add clip

**Tier-2: Multi-Step Workflows** (3 tasks, created but MCP timeout issues)
- 4-6 tool calls in a coordinated workflow
- Test agent's ability to sequence operations
- Verification: Were all required tools called successfully?
- Examples: Sequence + clip + text + transition

**Tier-3: Complex Production Workflows** (5 tasks, designed here)
- 8-15+ tool calls with planning requirements
- Test agent's ability to compose complete edits with narrative/structural thinking
- Verification: Does the output match professional editing standards?
- Examples: Multi-scene story, trailer assembly, podcast edit

## Design Principles

### 1. Realistic Use Cases
Each task mirrors actual video editing workflows:
- **Multi-scene story**: Narrative content with scene structure
- **Color-graded montage**: Visual effects and speed manipulation
- **Podcast edit**: Audio-centric with lower thirds and B-roll
- **Social cutdown**: Vertical format optimization with rapid pacing
- **Trailer assembly**: Dramatic structure with acts, audio design, and effects

### 2. Compositional Complexity
Tier-3 tasks require the agent to:
- Understand temporal relationships (what comes before/after)
- Manage multiple tracks and layers
- Coordinate timing between elements (text appearing during clips)
- Apply effects in context (color grade for mood, speed for pacing)

### 3. Planning Requirements
The agent must:
- Break down high-level goals into executable steps
- Determine the correct order of operations
- Handle dependencies (can't add transition before clips exist)
- Verify intermediate results before proceeding

### 4. Professional Judgement
Tasks test whether the agent can:
- Choose appropriate effects for the use case
- Apply timing that feels natural (not just technically correct)
- Layer elements properly (titles over video, B-roll with opacity)
- Create coherent structure (acts in a trailer, segments in a podcast)

## Task Complexity Metrics

| Task | Est. Steps | Tracks Used | Tool Calls | Effects/Transitions | Unique Challenges |
|------|-----------|-------------|------------|---------------------|-------------------|
| Multi-Scene Story | 9 | 4 (V0, V2, V3 + markers) | 15+ | 2+ transitions | Narrative sequencing, markers |
| Color-Graded Montage | 8 | 3 (V0, V2, audio) | 20+ | 3+ transitions + effects | Speed changes, color work, effects |
| Podcast Edit | 9 | 4 (A0, V0, V1, V2, V3) | 18+ | 2+ fades | Audio mixing, keyframes, segments |
| Social Cutdown | 11 | 4 (V0, V2, V3 + settings) | 20+ | Multiple cuts + transitions | Vertical format, rapid pacing, splits |
| Trailer Assembly | 8 | 5 (V0, V1, V2, V3, A1) | 25+ | 4+ splits + transitions | Act structure, audio dynamics, drama |

## Verification Strategy

Tier-3 verification must check:
1. **Structural correctness**: Required elements exist (clips, text, markers)
2. **Temporal accuracy**: Elements appear at correct times
3. **Effect application**: Color, speed, opacity changes applied
4. **Track organization**: Elements on correct tracks (overlay vs. base)
5. **Completeness**: All segments/acts/sections present

Unlike tier-1/2 which check "was this tool called?", tier-3 checks "does the output exhibit the intended structure?"

## Implementation Notes for tier3_test.py

When implementing tests:
- Use `get_full_sequence_info` for deep verification (clips, transitions, effects)
- Count clips after splits to verify editing operations
- Check text overlay count and timing via timeline summary
- Verify effects applied via `list_clip_effects`
- Use markers to validate structural organization
- Check sequence settings for format/resolution requirements
- Increase MAX_TURNS to 30-40 for complex tasks

## Success Criteria

A tier-3 task passes if:
1. All required structural elements are present
2. Timing relationships are correct (within 0.5s tolerance)
3. Effects and transitions are applied
4. The output represents a coherent, professional-looking edit

The agent demonstrates tier-3 capability when it can autonomously plan and execute these workflows without step-by-step guidance, using only the high-level task description.

## Future Extensions

Potential tier-4 benchmarks could test:
- Cross-sequence workflows (create master sequence from sub-sequences)
- Advanced color grading with LUTs and secondary corrections
- Multi-camera editing with sync
- Motion graphics integration with keyframe animation
- Export optimization with preset selection
- Error recovery and undo/redo strategies
