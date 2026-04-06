Add a text title overlay to the active Premiere Pro timeline with these exact parameters:

- Text: "HELLO WORLD"
- Video track index: 1
- Start time: 5 seconds
- Duration: 3 seconds

Steps:
1. Check the active sequence with `get_active_sequence`.
2. Add the text overlay using `add_text_overlay` with the parameters above.
3. Verify the overlay was added by calling `get_timeline_summary`.
