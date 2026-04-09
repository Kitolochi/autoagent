# Tier Comparison: Complexity Escalation

## Quick Reference Table

| Dimension | Tier 1 | Tier 2 | Tier 3 |
|-----------|--------|--------|--------|
| **Tool Calls** | 1-3 | 4-6 | 8-25+ |
| **MAX_TURNS** | 10 | 20 | 30-40 |
| **Tracks Used** | 1-2 | 2-3 | 3-5 |
| **Planning Required** | None | Minimal | Extensive |
| **Verification Depth** | Tool success | Tool sequence | Structural correctness |
| **Passing Tests** | 4/4 ✅ | 0/3 ⚠️ | 0/5 🆕 |

## Capability Progression

### Tier 1: Can You Press the Button?
- **Test**: Individual tool functionality
- **Agent Skill**: Tool calling
- **Example**: "Create a sequence named X"
- **Failure Mode**: Tool doesn't work or returns error
- **Human Equivalent**: Intern learning Premiere's buttons

### Tier 2: Can You Follow a Recipe?
- **Test**: Multi-step workflows with fixed sequences
- **Agent Skill**: Sequential operation
- **Example**: "Create sequence, add clip, add text, add transition"
- **Failure Mode**: Steps out of order, missing steps, MCP timeout
- **Human Equivalent**: Junior editor following a tutorial

### Tier 3: Can You Build the Dish?
- **Test**: Complete production workflows requiring composition
- **Agent Skill**: Planning, structure, timing, effects
- **Example**: "Create a podcast edit with intro, segments, lower thirds, B-roll"
- **Failure Mode**: Missing structure, poor timing, wrong track placement
- **Human Equivalent**: Professional editor given creative brief

## Complexity Examples

### Tier 1 Example: Add Text
```
Task: Add text overlay "HELLO" to timeline
Steps: 1
Tools: add_text_overlay
Verification: Text exists
```

### Tier 2 Example: Basic Edit
```
Task: Create sequence with clip, text, and transition
Steps: 4
Tools: create_sequence, create_bars_and_tone, add_to_timeline, add_text_overlay, execute_extendscript
Verification: All tools called successfully
```

### Tier 3 Example: Podcast Edit
```
Task: Create podcast-style edit with intro music, segments, lower thirds, B-roll
Steps: 9+
Tools: create_sequence, create_bars_and_tone (3x), add_to_timeline (3x), trim_clip, 
       add_marker (4x), add_text_overlay (3x), set_clip_opacity, adjust_audio_levels (2x),
       execute_extendscript, split_clip, get_full_sequence_info
Verification: 
  - Correct track organization (audio/video/overlay)
  - Markers at segment boundaries
  - Text overlays at correct times
  - B-roll with opacity
  - Audio levels adjusted
  - Clip split at correct time
```

## Decision-Making Complexity

### Tier 1: No Decisions
- Task specifies exact parameters
- Agent just calls the tool with given args
- No planning or sequencing required

### Tier 2: Sequence Decisions
- Task specifies steps but agent must order them
- Must handle dependencies (can't add transition before clip exists)
- Minimal timing decisions (when to place clips)

### Tier 3: Compositional Decisions
- Task gives outcome, agent plans execution
- Must decide track placement (which layer for each element)
- Must coordinate timing (text appearing during clips)
- Must apply effects appropriately (color for mood, speed for pacing)
- Must structure content (acts, segments, scenes)

## Tool Usage Patterns

### Tier 1: Single-Shot
```
User: "Add text X"
Agent: add_text_overlay(...)
Agent: Done
```

### Tier 2: Chain
```
User: "Create basic edit"
Agent: create_sequence(...)
Agent: create_bars_and_tone()
Agent: add_to_timeline(...)
Agent: add_text_overlay(...)
Agent: execute_extendscript(transition)
Agent: Done
```

### Tier 3: Plan-Execute-Verify Loop
```
User: "Create podcast edit"
Agent: [internal planning]
Agent: create_sequence(...)
Agent: create_bars_and_tone() // intro music
Agent: add_to_timeline(...track 0)
Agent: trim_clip(...5s duration)
Agent: create_bars_and_tone() // main content
Agent: add_to_timeline(...track 0, start 5s)
Agent: create_bars_and_tone() // B-roll
Agent: add_to_timeline(...track 1, start 20s)
Agent: set_clip_opacity(...80%)
Agent: add_marker("Intro", 5s)
Agent: add_marker("Topic 1", 15s)
Agent: add_text_overlay("HOST: Alex Chen", track 2, 7-12s)
Agent: add_text_overlay("Episode 42", track 3, 5-10s)
Agent: adjust_audio_levels(intro, -12dB)
Agent: split_clip(main, 30s)
Agent: get_full_sequence_info() // verify
Agent: Done
```

## Verification Complexity

### Tier 1: Boolean
```python
# Did the tool succeed?
if "ERROR" not in result:
    return PASS
```

### Tier 2: Set Membership
```python
# Were all required tools called?
required = ["create_sequence", "add_to_timeline", "add_text_overlay"]
called = [t["tool"] for t in trajectory if not t["result"].startswith("ERROR")]
if set(required).issubset(set(called)):
    return PASS
```

### Tier 3: Structural Validation
```python
# Does the output have the right structure?
info = get_full_sequence_info()
checks = [
    len(info["videoTracks"][0]["clips"]) >= 2,  # Multiple clips
    len(info["videoTracks"][1]["clips"]) >= 1,  # B-roll overlay
    info["markers"]["count"] >= 4,               # Segment markers
    any("HOST" in clip["name"] for track in info["videoTracks"] 
        for clip in track["clips"]),             # Lower third present
    # ... more structural checks
]
if all(checks):
    return PASS
```

## Failure Analysis

### Tier 1 Failures (All Resolved ✅)
- MCP connection issues → fixed with persistent session
- Tool parameter mismatches → fixed with correct schemas
- Premiere state issues → fixed with verification calls

### Tier 2 Failures (Current Blockers ⚠️)
- MCP timeout on long workflows → needs investigation
- State accumulation between tests → needs cleanup
- Transition tool bugs → worked around with execute_extendscript

### Tier 3 Anticipated Failures (To Be Tested 🆕)
- Planning failures: Wrong order of operations
- Timing errors: Clips/text not aligned correctly
- Track placement: Elements on wrong video/audio tracks
- Effect application: Wrong clips or parameters
- Structural errors: Missing acts/segments/sections
- Verification gaps: Agent thinks it's done but output incomplete

## Success Metrics by Tier

### Tier 1: Pass Rate
- Target: 100% (foundational capability)
- Current: 4/4 (100%) ✅

### Tier 2: Workflow Completion Rate
- Target: 80%+ (acceptable for composite workflows)
- Current: 0/3 (blocked by MCP timeout, not agent failure)

### Tier 3: Professional Quality Rate
- Target: 60%+ (demonstrates planning capability)
- Current: Not yet tested
- Success Criteria:
  - 3/5 tasks = Agent has basic compositional capability
  - 4/5 tasks = Agent is production-ready
  - 5/5 tasks = Agent demonstrates professional-level planning
