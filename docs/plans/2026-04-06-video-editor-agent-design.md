# Video Editor Agent — Design Document

**Date:** 2026-04-06
**Status:** Approved

## Goal

Build an AutoAgent harness where the agent-under-test is a professional video
editor operating natively in Premiere Pro (via MCP) and After Effects (via
ExtendScript bridge). The meta-agent iterates on the harness to improve editing
quality across graduated benchmark tasks.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  AutoAgent Meta-Loop (program.md)                    │
│  Iterates on harness, runs benchmarks, scores        │
├─────────────────────────────────────────────────────┤
│  Editor Agent Harness (agent.py)                     │
│  System prompt + tools + knowledge base              │
│  Routes through ccproxy → Claude Sonnet 4.6          │
├──────────────────────┬──────────────────────────────┤
│  Premiere MCP        │  AE ExtendScript Bridge       │
│  200+ timeline tools │  Composition building         │
│  Cuts, effects, audio│  Motion graphics, titles      │
└──────────────────────┴──────────────────────────────┘
```

All API calls route through the local ccproxy at `localhost:8741` using Claude
Pro OAuth. No API keys required. Model defaults to `claude-sonnet-4-6`,
configurable via `AUTOAGENT_MODEL` env var.

## Harness Design (agent.py)

### Tool Categories

**Premiere tools** — Exposed from the Premiere Pro MCP:
- Timeline: add_to_timeline, trim_clip, move_clip, split_clip, ripple_delete
- Effects: apply_effect, add_transition, color_correct, adjust_audio_levels
- Project: import_media, create_sequence, create_bin
- Inspection: get_active_sequence, get_timeline_summary, get_clip_properties

**After Effects tools** — Custom wrappers around the ExtendScript bridge:
- ae_create_comp — create composition with dimensions/duration
- ae_add_text_layer — add and style text layers
- ae_add_shape_layer — add shapes with properties
- ae_apply_effect — apply effects with parameters
- ae_render_comp — render to file for Premiere import

**Knowledge tools** — Query the knowledge base on demand:
- lookup_technique(query) — search video-engagement-techniques catalog
- lookup_ae_pattern(query) — search ae-extendscript-patterns for gotchas

### System Prompt Structure

1. Role: Professional video editor in Premiere Pro and After Effects
2. Core workflow: Inspect → Plan → Execute → Verify
3. Key rules: Check timeline state before editing. Verify after changes.
4. Technique reference: Top-20 compressed techniques from knowledge base
5. AE gotchas: Critical patterns from ae-extendscript-patterns

## Benchmark Tasks

### Tier 1 — Atomic Operations (10-15 tasks)

Single editing operations with deterministic verification.

Examples:
- Import a clip and place it on V1 at a specific timecode
- Add a cross dissolve between two clips
- Add a centered text title at a given time
- Apply Lumetri color correction with specific parameters
- Set audio levels on a track

Verification: MCP inspection tools check clip count, position, effect
presence, parameter values. Binary pass/fail.

### Tier 2 — Sequences (5-8 tasks)

Multi-step sequences that build a short edit.

Examples:
- Build a 15s intro: logo reveal → feature shots → CTA with transitions
- Arrange clips with J-cuts matching beat markers
- Create a lower-third in AE, import and place in Premiere

Verification: Structure checks (clip count, ordering, durations within
tolerance) + effect checks. Binary pass/fail.

### Tier 3 — Creative Edits (3-5 tasks)

Open-ended tasks requiring editorial judgment.

Examples:
- Build a product demo from 5 screenshots and a music track
- Tighten a rough cut: remove dead air, add transitions, fix audio

Verification: Structural requirements + LLM-as-judge scoring the timeline
against the brief. Score 0.0-1.0.

### Tier 4 — Full Pipeline (future)

Concept to finished timeline with visual generation. Deferred until
Tiers 1-3 are passing.

## Verification Approach

Verifiers run host-side (not in Docker) since tasks require a live Premiere
instance. The test script:

1. Calls Premiere MCP inspection tools to read project state
2. Checks against expected conditions (clip count, positions, effects, etc.)
3. Returns score to results.tsv

## File Changes

### Modified
- `agent.py` — Video editor harness with Premiere/AE tools + knowledge base
- `program.md` — Video editing directive and experiment loop
- `pyproject.toml` — Dependencies for AE bridge communication

### Added
- `tasks/` — Benchmark tasks by tier
- `knowledge/` — Compressed reference material from video-engagement-techniques
  and ae-extendscript-patterns
- `tools/premiere.py` — Premiere MCP tool wrappers
- `tools/ae_bridge.py` — AE ExtendScript bridge wrappers
- `tools/knowledge.py` — Knowledge base lookup tool

### Unchanged
- AutoAgent experiment loop structure
- Proxy setup (ccproxy → Claude Sonnet 4.6)
- Harbor adapter boundary in agent.py
- results.tsv tracking

## Key Constraint

Tasks run host-side, not in Docker containers. The agent communicates with
live Premiere Pro and After Effects instances. Both applications must be
running during benchmark execution.

## Model Strategy

Start with Sonnet 4.6 for fast iteration on Tier 1-2 tasks. Graduate to
Opus 4.6 when Tier 3 creative tasks require deeper reasoning.
