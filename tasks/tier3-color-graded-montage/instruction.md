Create a color-graded montage with multiple clips, speed variations, and visual effects.

Context:
This tests the agent's ability to work with visual effects, speed manipulation, and color correction across multiple clips - essential video editing techniques for professional output.

Steps:
1. Create a new sequence named "Montage_[timestamp]"
2. Add 4 Bars and Tone clips to track 0 at positions: 0s, 3s, 6s, 9s
3. Apply speed changes: Set clip 2 (at 3s) to 2x speed, clip 4 (at 9s) to 0.5x speed
4. Apply color correction to all clips:
   - Clip 1 (at 0s): brightness +20, contrast +10, saturation 120
   - Clip 2 (at 3s): brightness -10, temperature +15 (warm look)
   - Clip 3 (at 6s): saturation 80 (desaturated look)
   - Clip 4 (at 9s): brightness +10, contrast +20, saturation 110 (vibrant)
5. Add Cross Dissolve transitions between all clips
6. Add a title overlay "MONTAGE" on track 2, from 0-2 seconds, with 50% opacity
7. Add an effect: Apply "Gaussian Blur" to clip 3 (at 6s) for a dreamy look
8. Adjust audio: Lower the audio level on all clips to -6dB

Verification:
- Sequence exists with 4 clips on track 0
- At least 3 transitions between clips
- Speed changes applied (verifiable via get_clip_properties or get_full_sequence_info)
- Color correction applied to multiple clips (check clip properties or effects list)
- Gaussian Blur effect applied to clip 3
- Title overlay exists on track 2
- Audio levels adjusted on audio track

Required Tools:
- create_sequence
- create_bars_and_tone (called 4 times)
- add_to_timeline (called 4 times)
- speed_change (called 2 times)
- color_correct (called 4 times)
- execute_extendscript (for transitions, since add_transition_to_clip may have bugs)
- add_text_overlay
- set_clip_opacity
- apply_effect
- adjust_audio_levels (called 4 times)
- get_full_sequence_info (for verification)
