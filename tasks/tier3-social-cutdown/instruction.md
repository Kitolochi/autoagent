Create a social media cutdown from a longer sequence, optimized for vertical format with captions and timed cuts.

Context:
This tests the agent's ability to work with sequence settings, aspect ratios, precise trimming, and the rapid pacing required for social media content.

Steps:
1. Create a new sequence named "Social_[timestamp]" with vertical format (1080x1920)
2. Import or create source content: Add Bars and Tone clip to track 0 starting at 0s (represents source footage)
3. Trim the clip to extract the best 15 seconds (trim start by 5s, trim end to make total duration 15s)
4. Add attention-grabbing opening: Text overlay "WAIT FOR IT..." on track 2, from 0-2 seconds
5. Add timed captions simulating subtitles:
   - Text "This is amazing" on track 3, from 2-5 seconds
   - Text "Watch what happens" on track 3, from 5-8 seconds
   - Text "Incredible results" on track 3, from 8-11 seconds
   - Text "Try it yourself" on track 3, from 11-14 seconds
6. Add visual punch cuts: Split the main clip at 4s, 7s, and 10s to create jump cuts
7. Add speed ramp: Speed up middle section (clip at 7s) to 1.5x
8. Add zoom effect: Scale clip at 10s to 120% (simulating punch-in)
9. Add CTA (call to action): Text overlay "FOLLOW FOR MORE" on track 2, from 13-15 seconds
10. Color grade for social: Apply high contrast and saturation boost to all clips
11. Add engaging transition: Zoom or whip transition between segments using execute_extendscript

Verification:
- Sequence exists with vertical resolution (1080x1920)
- Source clip trimmed to approximately 15 seconds
- At least 4 clips on track 0 (after splits at 4s, 7s, 10s)
- Multiple text overlays on tracks 2 and 3 (opening hook + 4 captions + CTA)
- Speed change applied to middle section
- Scale/zoom applied to clip (verifiable via clip properties)
- Color correction applied for social media look
- Transitions between segments

Required Tools:
- create_sequence (with vertical preset or custom settings)
- create_bars_and_tone
- add_to_timeline
- trim_clip
- add_text_overlay (called 6 times: hook + 4 captions + CTA)
- split_clip (called 3 times at 4s, 7s, 10s)
- speed_change
- execute_extendscript (for scale/position changes and transitions)
- color_correct (applied to multiple clips)
- get_full_sequence_info (for verification)
- get_sequence_settings (to verify vertical format)
