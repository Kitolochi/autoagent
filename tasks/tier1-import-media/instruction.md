Import a media file into the current Premiere Pro project.

Parameters:
- File path: "C:/Users/chris/Videos/sample.mp4" (test file - agent should check if exists)
- Bin path: "" (root bin)

Steps:
1. Check if the file exists and is accessible.
2. Import the media using `import_media` with the file path.
3. Verify the import by calling `list_project_items` or `get_project_info`.
