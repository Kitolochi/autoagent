Add a project item to the timeline at a specific position.

Parameters:
- Item: First available media item in the project (use get_project_info to find)
- Track index: 0
- Start time: 0 seconds

Steps:
1. Call `get_project_info` to find available media items.
2. Add the first media item to the timeline using `add_to_timeline`.
3. Verify the clip was added by calling `get_timeline_summary`.
