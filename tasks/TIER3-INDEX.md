# Tier-3 Benchmark Tasks Index

## Task List

### 1. tier3-multi-scene-story
**Complexity**: Medium  
**Focus**: Narrative sequencing, scene structure, markers  
**Key Elements**: 3 scenes with transitions, opening/closing titles, scene labels, timeline markers  
**Tools Required**: 15+ calls across create_sequence, create_bars_and_tone, add_to_timeline, add_text_overlay, transitions, markers  

### 2. tier3-color-graded-montage
**Complexity**: Medium-High  
**Focus**: Visual effects, color correction, speed manipulation  
**Key Elements**: 4 clips with individual color grades, speed ramps (2x, 0.5x), Gaussian Blur effect, opacity control  
**Tools Required**: 20+ calls across sequence creation, clips, speed_change, color_correct, apply_effect, audio mixing  

### 3. tier3-podcast-edit
**Complexity**: High  
**Focus**: Audio-centric editing, lower thirds, segment organization  
**Key Elements**: Intro music bed, main content, B-roll overlay, lower thirds, segment markers, audio keyframes  
**Tools Required**: 18+ calls across tracks, trimming, markers, text overlays, opacity, audio levels, split  

### 4. tier3-social-cutdown
**Complexity**: High  
**Focus**: Vertical format, rapid pacing, social media optimization  
**Key Elements**: 1080x1920 sequence, 15s duration, jump cuts (3 splits), timed captions (4), speed ramp, zoom effect, CTA  
**Tools Required**: 20+ calls across sequence settings, trimming, splits, text overlays, speed/scale changes, color grading  

### 5. tier3-trailer-assembly
**Complexity**: Very High  
**Focus**: Dramatic narrative structure, act-based composition, audio design  
**Key Elements**: 4-act structure, 8+ title cards, rapid cuts in Act 2, speed ramps, overlay track, audio dynamics, markers  
**Tools Required**: 25+ calls across multi-track composition, splits, overlays, audio keyframes, effects, transitions  

## Recommended Testing Order

1. **tier3-multi-scene-story** - Start here, tests basic multi-step narrative planning
2. **tier3-color-graded-montage** - Adds visual effects and speed manipulation
3. **tier3-podcast-edit** - Introduces audio complexity and B-roll layering
4. **tier3-social-cutdown** - Tests format adaptation and rapid editing
5. **tier3-trailer-assembly** - Capstone test of all capabilities combined

## Quick Stats

- **Total Tasks**: 5
- **Estimated Total Tool Calls**: 98+
- **Unique Tools Tested**: 20+
- **Tracks Used**: Up to 5 simultaneous tracks
- **Average Task Complexity**: 8-11 steps, 18-25 tool calls

## Test Execution Notes

- Set MAX_TURNS to 30-40 for tier-3 (vs. 20 for tier-2, 10 for tier-1)
- MCP timeout may be an issue - tier-2 had timeouts, tier-3 will stress this further
- Consider adding intermediate verification steps in prompts
- Use `get_full_sequence_info` for comprehensive verification
- Test on fresh Premiere project for each task to avoid state pollution

## Success Metrics

Pass rate targets:
- **60% (3/5)** = Agent has basic compositional capability
- **80% (4/5)** = Agent is production-ready for structured workflows
- **100% (5/5)** = Agent demonstrates professional-level video editing planning

## Related Files

- Task definitions: `tasks/tier3-*/instruction.md`
- Design philosophy: `tasks/TIER3-DESIGN.md`
- Test implementation: `tier3_test.py` (to be created)
- Tier-1 passing: `simple_test_v2.py` (4/4 passing)
- Tier-2 blocked: `tier2_test.py` (3 tasks, MCP timeout issues)
