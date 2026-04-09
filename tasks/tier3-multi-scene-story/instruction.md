Create a multi-scene narrative sequence with opening title, three distinct scenes with transitions, and an end card.

Context:
This tests the agent's ability to plan and execute a complete narrative structure with multiple scenes, requiring sequencing, timing coordination, and compositional awareness.

Steps:
1. Create a new sequence named "Story_[timestamp]"
2. Add opening title card: Text overlay "CHAPTER ONE" on track 2, from 0-3 seconds
3. Scene 1: Add Bars and Tone to track 0 starting at 0 seconds
4. Scene 2: Add another Bars and Tone clip to track 0 starting at 8 seconds
5. Scene 3: Add a third Bars and Tone clip to track 0 starting at 16 seconds
6. Add Cross Dissolve transitions between all three scenes (at scene boundaries)
7. Add scene labels: Text overlays on track 3 saying "Morning" (1-2s), "Afternoon" (9-10s), "Evening" (17-18s)
8. Add end card: Text overlay "THE END" on track 2, from 23-26 seconds
9. Add markers at key moments: "Scene 1" at 0s, "Scene 2" at 8s, "Scene 3" at 16s, "End" at 23s

Verification:
- Sequence exists with 3 Bars and Tone clips on track 0
- At least 2 transitions between clips (verifiable via get_full_sequence_info)
- Text overlays on tracks 2 and 3 at specified times
- At least 4 markers placed on the timeline
- Total sequence duration approximately 26 seconds

Required Tools:
- create_sequence
- create_bars_and_tone (called 3 times)
- add_to_timeline (called 3 times)
- add_text_overlay (called 5 times total: opening, 3 scene labels, end card)
- execute_extendscript or add_transition_to_clip (for transitions)
- add_marker (called 4 times)
- get_full_sequence_info (for verification)
