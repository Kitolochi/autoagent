# AutoAgent Video Editor Project Status

**Last Updated:** 2026-04-09  
**Current Branch:** main  
**Latest Commit:** 2f0621a (feat: add tier-2 multi-step composite workflow tests)

## Project Overview

AutoAgent Video Editor is an autonomous agent engineering harness for building a professional AI video editor that operates natively in Adobe Premiere Pro via MCP (Model Context Protocol). The meta-agent iteratively improves the agent harness in `agent.py` by running benchmarks, diagnosing failures, and implementing general improvements.

**Core Approach:**
- Agent receives natural-language editing instructions
- Operates live Premiere Pro instance through MCP tools (port 3001)
- Task verifiers inspect Premiere project state to evaluate success
- Meta-agent hill-climbs on total passed tasks

**Architecture:**
- `agent.py` - Single-file harness with editable prompt/tools and fixed Harbor adapter
- `program.md` - Meta-agent instructions and directive (human-edited)
- `tasks/` - Harbor-format benchmark tasks across 3 tiers
- `tools/premiere.py` - 32 Premiere MCP tool wrappers
- `tools/knowledge.py` - Lookup tools for embedded knowledge base
- `knowledge/` - techniques.md (20 video engagement patterns) + ae-gotchas.md

## Benchmark Tiers

### Tier 1: Atomic Operations (6 tasks defined)
Single Premiere Pro operation per task. Tests basic tool calling.

**Defined Tasks:**
1. `tier1-create-sequence` - Create a new sequence
2. `tier1-add-clip` - Add project item to timeline
3. `tier1-add-title` - Add text overlay using MOGRT
4. `tier1-add-transition` - Add Cross Dissolve transition via ExtendScript
5. `tier1-import-media` - Import media file to project
6. `tier1-adjust-audio` - Adjust audio levels on clip

**Status:** Tasks defined, instruction.md files present. Harbor integration attempted but not verified passing.

### Tier 2: Multi-Step Workflows (3 tasks defined)
Composite operations requiring multiple tools in sequence.

**Defined Tasks:**
1. `tier2-basic-edit` - Sequence + clip + text overlay + transition
2. `tier2-transition-between-clips` - Two clips with transition between them
3. `tier2-titled-sequence` - Multiple text overlays on timeline

**Status:** Tasks defined, instruction.md files present. Not yet tested in Harbor harness.

### Tier 3: Complex Production (5 tasks defined)
Real-world editing scenarios requiring planning and multi-step execution.

**Defined Tasks:**
1. `tier3-color-graded-montage` - instruction.md exists
2. `tier3-multi-scene-story` - instruction.md exists
3. `tier3-podcast-edit` - folder exists, no instruction.md verified
4. `tier3-social-cutdown` - folder exists, no instruction.md verified
5. `tier3-trailer-assembly` - folder exists, no instruction.md verified

**Status:** Partially defined. Not yet implemented or tested.

## Test Results Summary

### Direct API Tests (simple_test_v2.py)
Standalone tier-1 benchmark using direct OpenAI API calls (no Harbor harness).

**Latest Known Results:** 3/4 passing (commit 013908d)
- ✅ create_sequence
- ✅ add_text_overlay
- ✅ add_clip_to_timeline (create_bars_and_tone + add_to_timeline)
- ❓ add_transition (status unclear, ExtendScript-based)

**Blocker:** Cannot run currently - missing `openai` module in active environment despite being in pyproject.toml. Likely needs `uv sync` or `.venv` activation.

### Harbor Integration Tests
**Latest Run:** 2026-04-07 16:48-16:53 (jobs/latest/)

**Results:** 0/3 passing, 1 error
- ❌ tier1-add-title__wJShSwQ - reward 0.0
- ❌ tier1-create-sequence__VuLc4ie - reward 0.0  
- ⚠️ tier1-add-transition__b6qA5LF - BadRequestError

**Issues:**
- MCP session cleanup errors (RuntimeError: cancel scope task mismatch)
- All tasks scored 0.0, indicating verifier or agent execution failure
- Only 3 tier-1 tasks attempted (not all 6 defined tasks)

### Tier-2 Standalone Tests (tier2_test.py)
Created in commit 2f0621a. Not yet executed.

**Defined Tests:**
1. test_basic_edit - 5 required tools
2. test_two_clips_transition - checks for 2x create_bars_and_tone + 2x add_to_timeline
3. test_titled_sequence - checks for 2x add_text_overlay

**Status:** Code written but not run. Needs environment setup + Premiere MCP running.

## Known Issues

### Critical
1. **Environment Setup** - `openai` package not importable despite being in pyproject.toml. Likely missing `uv sync`.
2. **Harbor Integration** - Last run produced all 0.0 scores. Need to diagnose verifier vs agent failure.
3. **MCP Session Management** - Async cleanup errors in streamable_http_client exit stack. Non-blocking but noisy.

### Configuration
1. **Proxy Setup** - Uses ccproxy at localhost:8741 with Claude Pro OAuth (documented in memory/proxy_setup.md)
2. **Premiere MCP Port** - Changed to 3001 (commit 8eaabe0) to avoid Remotion conflict
3. **Model** - claude-sonnet-4-6 via AUTOAGENT_MODEL env var

### AE Bridge Integration
1. **Panel not installed** - `mcp-bridge-auto.jsx` not found in AE 2025 or 2026 ScriptUI Panels. Run `node install-bridge.js` with admin rights.
2. **Protocol fixed** - http-server.js rewritten to use panel's JSON protocol (ae_command.json / ae_mcp_result.json) instead of incompatible per-id cmd_*.jsx files.
3. **runScript command added** - Panel now supports arbitrary JSX via `runScript` command for `run_ae_script` tool.
4. **Directories aligned** - Both server and panel use `C:/Users/chris/Documents/ae-mcp-bridge` (prior "C:/tmp" note was inaccurate).

### Tool Issues
1. **add_transition_to_clip** - Known bug, workaround uses execute_extendscript with QE DOM (commit 7f3d673)
2. **ExtendScript Execution** - Must use ES3 syntax (var not let/const), requires __result/__error wrappers

## Dependencies

**Core:**
- openai-agents (OpenAI Agents SDK)
- claude-agent-sdk
- harbor (benchmark framework)
- openai>=2.30.0 (added in commit 0d89093)
- mcp (Model Context Protocol client)

**Prerequisites:**
1. ccproxy running at localhost:8741
2. Premiere Pro with CEP MCP bridge plugin
3. Premiere MCP HTTP server at localhost:3001
4. Python 3.12+, uv, Docker

## Recent Changes (Last 10 Commits)

1. **2f0621a** - feat(benchmark): add tier-2 multi-step composite workflow tests
2. **0990315** - feat(benchmark): add tier-1 test for add_clip_to_timeline
3. **679f5e6** - chore(git): ignore uv.lock per lock file policy
4. **0d89093** - chore(deps): add openai package for direct API benchmark tests
5. **7f3d673** - refactor(benchmark): replace ExtendScript clip test with add_text_overlay tool
6. **013908d** - fix(benchmark): tier-1 passing 3/3 with direct API loop
7. **8eaabe0** - fix(tools): use port 3001 for Premiere MCP to avoid Remotion conflict
8. **282b74b** - feat(tasks): add 3 tier-1 benchmark tasks for atomic Premiere Pro operations
9. **52c3bc9** - feat(program): rewrite directive for video editor agent
10. **7e85ba8** - feat(agent): rewrite harness for video editor with Premiere/AE/knowledge tools

## Next Steps

### Immediate (Unblock Testing)
1. Run `uv sync` to install dependencies including openai package
2. Verify Premiere MCP connectivity: `curl http://localhost:3001/mcp`
3. Start ccproxy: `cd C:\Users\chris\llm-proxy && ccproxy serve --config config.toml`
4. Run simple_test_v2.py to verify tier-1 baseline
5. Run tier2_test.py to establish tier-2 baseline

### Harbor Integration
1. Debug why last Harbor run produced all 0.0 scores
2. Check verifier code for tier-1 tasks
3. Fix MCP session cleanup warnings
4. Run full tier-1 suite (6 tasks) through Harbor
5. Initialize results.tsv with baseline run

### Benchmark Expansion
1. Complete tier-3 task definitions (3 missing instruction.md files)
2. Add verifier.py to all task directories
3. Document expected Premiere project state for each task
4. Consider adding tier-2 and tier-3 to Harbor runs once tier-1 passes

### Harness Improvements
1. Review agent.py system prompt effectiveness
2. Consider compound tools for common multi-step operations
3. Add verification sub-agent to check timeline state after edits
4. Improve error recovery for MCP tool failures
5. Add After Effects bridge for motion graphics workflows

## Files Modified (Uncommitted)

- `simple_test_v2.py` - Modified (lines changed unknown)
- `uv.lock` - Untracked (ignored per commit 679f5e6)

## Success Metrics

**Primary:** Number of passed tasks  
**Secondary:** avg_score (passed / total in binary-pass setting)  
**Simplicity Criterion:** Equal performance with simpler code is a real improvement

**Target:** Maximize tier-1 pass rate first (6/6), then tier-2 (3/3), then tier-3 (5/5)

## Resources

- **Project Root:** C:\Users\chris\autoagent
- **Premiere MCP:** C:\Users\chris\lifeautomation\premiere-pro-mcp\dist\http-server.js
- **Proxy:** C:\Users\chris\llm-proxy (ccproxy)
- **Memory:** ~/.claude/projects/C--Users-chris-autoagent/memory/

## Notes

- Serial execution required (`-n 1` in Harbor) - all tasks share single Premiere instance
- No results.tsv file exists yet - needs initialization on first valid run
- Knowledge base provides 20 video engagement techniques + AE gotchas for agent context
- Fork of kevinrgu/autoagent, adapted for Premiere Pro video editing workflows
