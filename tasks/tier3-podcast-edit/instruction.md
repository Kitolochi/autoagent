Create a podcast-style edit with intro music, multiple segments, lower thirds, and outro.

Context:
This tests the agent's ability to handle audio-centric editing with visual overlays, segment management, and the layered composition typical of podcast videos.

Steps:
1. Create a new sequence named "Podcast_[timestamp]"
2. Add intro music bed: Bars and Tone on audio track 0, starting at 0s, trimmed to 5 seconds duration
3. Add main content: Bars and Tone on video track 0, starting at 5s (represents main camera)
4. Add segment markers to organize content:
   - "Intro" marker at 5s
   - "Topic 1" marker at 15s
   - "Topic 2" marker at 30s
   - "Outro" marker at 45s
5. Add lower third graphics:
   - Text overlay "HOST: Alex Chen" on track 2, from 7-12 seconds
   - Text overlay "GUEST: Dr. Sam Rivera" on track 2, from 17-22 seconds
   - Text overlay "Episode 42: AI in 2025" on track 3, from 5-10 seconds (persistent info)
6. Add B-roll overlay: Second Bars and Tone clip on track 1 (overlay track), from 20-28 seconds, with 80% opacity
7. Audio mixing:
   - Reduce intro music to -12dB after first 3 seconds (fade down for voice)
   - Main content audio at -3dB
   - Add audio keyframes at 3s (transition point)
8. Add fade transitions: Fade in at sequence start, fade out at sequence end (45-47s)
9. Split main content clip at 30s to create segment break

Verification:
- Sequence exists with audio and video content across multiple tracks
- At least 4 markers placed for segment organization
- Multiple text overlays on tracks 2 and 3 at specified times
- B-roll clip on track 1 with reduced opacity
- Audio levels adjusted (intro music and main content)
- Clip split at 30s (verifiable via clip count on track 0)
- Transitions at start and end

Required Tools:
- create_sequence
- create_bars_and_tone (called 3 times: intro, main, B-roll)
- add_to_timeline (called 3 times)
- trim_clip (to make intro music 5s)
- add_marker (called 4 times)
- add_text_overlay (called 3 times)
- set_clip_opacity (for B-roll)
- adjust_audio_levels (called 2 times)
- execute_extendscript (for audio keyframes and fade transitions)
- split_clip (to split at 30s)
- get_full_sequence_info (for verification)
