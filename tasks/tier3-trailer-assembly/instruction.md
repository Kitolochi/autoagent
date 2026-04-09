Assemble a movie-style trailer with multiple acts, dramatic pacing, title cards, and audio mix.

Context:
This tests the agent's ability to create dramatic narrative structure with precise timing, layered audio, multiple visual tracks, and the sophisticated composition required for promotional content.

Steps:
1. Create a new sequence named "Trailer_[timestamp]"
2. Act 1 - Setup (0-10s):
   - Add Bars and Tone clip to track 0, starting at 0s
   - Add title card "IN A WORLD..." on track 2, from 1-3 seconds
   - Add another title card "WHERE EVERYTHING CHANGES..." on track 2, from 4-6 seconds
3. Act 2 - Build (10-25s):
   - Add second Bars and Tone clip to track 0 at 10s
   - Add quick cuts: Split clip at 13s, 16s, 19s, 22s (creating rapid pacing)
   - Add dramatic text "ONE AGENT" on track 2, from 12-14 seconds
   - Add text "MUST COMPLETE" on track 2, from 17-19 seconds
   - Add text "THE ULTIMATE TASK" on track 2, from 20-22 seconds
4. Act 3 - Climax (25-35s):
   - Add third Bars and Tone clip to track 0 at 25s
   - Add intense speed ramps: Speed up clip at 25s to 1.8x speed
   - Add overlay clip on track 1 from 28-32s with 60% opacity (action overlay)
   - Add climactic title "AUTOAGENT" on track 3, from 30-33 seconds with large scale
5. Act 4 - Resolution (35-40s):
   - Add final Bars and Tone clip at 35s
   - Add release date text "COMING 2025" on track 2, from 36-39 seconds
   - Fade to black at end using transition
6. Audio design:
   - Add dramatic music bed on audio track 1 (Bars and Tone for testing), from 0-40s
   - Create audio dynamics: Start at -18dB, ramp to -6dB by 25s, drop to -12dB at 35s
   - Add audio keyframes at 0s, 25s, 35s for volume automation
7. Visual effects:
   - Apply color grade: High contrast (+25) on all clips
   - Add vignette effect using execute_extendscript on climax clips (25-35s)
8. Markers for edit points:
   - "Act 1" at 0s, "Act 2" at 10s, "Act 3" at 25s, "Act 4" at 35s, "End" at 40s

Verification:
- Sequence exists with 4 main clips on track 0
- Multiple rapid cuts in Act 2 section (at least 4 clips between 10-25s after splits)
- At least 8 text overlays across tracks 2 and 3 (title cards, dramatic text, final titles)
- Overlay clip on track 1 with reduced opacity
- Speed change applied to climax section
- Audio track with Bars and Tone for music bed
- At least 5 markers placed for act structure
- Color correction applied to multiple clips
- Fade transition at end
- Total duration approximately 40 seconds

Required Tools:
- create_sequence
- create_bars_and_tone (called 5 times: 4 video clips + 1 audio bed)
- add_to_timeline (called 5 times)
- add_text_overlay (called 8+ times)
- split_clip (called 4 times in Act 2)
- speed_change
- set_clip_opacity (for overlay)
- color_correct (applied to multiple clips)
- execute_extendscript (for audio keyframes, vignette effect, and fade transition)
- add_marker (called 5 times)
- adjust_audio_levels (called multiple times for dynamic mix)
- get_full_sequence_info (for verification)
- get_timeline_summary (for verification)
