# Shiroi System Platform (SSP) Development Roadmap

This directory contains the roadmap files for the Shiroi System Platform, designed for real-time sharing and synchronization between Shiroi (GPT) and Gemini.

## Files:

*   `system_roadmap.json`: A simplified version of the roadmap, primarily focusing on past and current phases (up to v2.5).
*   `system_roadmap_extended.json`: The complete roadmap, including past, current, and future phases (up to v4.0).

## Editing Rules:

*   **Bidirectional Synchronization:** Both Shiroi (GPT) and Gemini are designed to read and update these files.
*   **Gemini's Role:** Gemini will primarily manage the structure and ensure consistency. It will update these files based on user instructions and its own development progress.
*   **Shiroi's Role:** Shiroi will primarily consume these files to understand its own development trajectory and philosophical vision. It may propose updates or new phases based on its self-analysis and emergent goals.
*   **Version Control:** All changes to these files will be tracked via Git. Please ensure proper commit messages.
*   **Data Integrity:** Maintain the JSON schema for both files. Invalid JSON may lead to system errors.
*   **Conflict Resolution:** In case of conflicts, manual review and resolution by a human operator may be required.
