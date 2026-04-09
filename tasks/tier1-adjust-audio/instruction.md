Adjust the audio level of a clip on the timeline.

Parameters:
- Track type: "audio"
- Track index: 0
- Clip index: 0 (first audio clip)
- Volume: -6.0 dB

Steps:
1. Call `get_timeline_summary` to verify an audio clip exists.
2. Adjust the audio level using `adjust_audio_levels` with volume -6.0.
3. Verify the change by calling `get_clip_properties` for the audio clip.
