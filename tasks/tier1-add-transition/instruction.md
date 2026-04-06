Add a Cross Dissolve transition to the first clip (clip index 0) on video track 0 of the active Premiere Pro timeline.

Parameters:
- Track index: 0
- Clip index: 0
- Transition name: "Cross Dissolve"
- Duration: 1.0 seconds
- Position: "start"

Steps:
1. Check the active sequence with `get_active_sequence` and `get_timeline_summary`.
2. Add the transition using `add_transition_to_clip` with the parameters above.
3. Verify the transition was applied by checking the timeline state.
