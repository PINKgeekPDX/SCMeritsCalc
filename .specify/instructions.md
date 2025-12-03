[CONTEXT]
- Project path: c:\Users\Administrator\Documents\projects\MeritsCalc
- Main UI source: src/meritscalc/ui.py
- Existing features: Dark-themed app calculating Star Citizen prison merits, time, and aUEC conversions with bidirectional updates.
- Current persistence: settings.json for configurations, the settings file as well as log files should be saved to: "Users\*user*\Documents\PINK\SCMeritCalc\settings.json" and "Users\*user*\Documents\PINK\SCMeritCalc\ScMeritCalc.log". App logging should maintain use of the same file everytime replacimng all of the contents with the logging only from the current app session (do not clear the log contents on app exit, do it when app logging is initialized at app start up.
- Goal: Replace existing UI with Python ImGui-based UI retaining all functionality.

[ROLE]
You are a Python GUI developer specialized in ImGui and Windows desktop applications.

[ACTION — USER OUTCOME]
Rebuild the MeritsCalc UI using Python ImGui on Windows platform with:
- https://github.com/hoffstadt/DearPyGui
- A precise borderless container window matching ImGui window dimensions,
- A functional title bar including minimize, maximize, close controls,
- Resizable window supporting resizing from all edges and corners,
- Draggable window via title bar with window repositioning,
- Optional aspect ratio enforcement controllable via settings toggle,
- Fully functional UI components (textboxes, buttons, tabs) with proper event handling, visual feedback, and state management,
- Comprehensive tab system with smooth animated transitions,
- Persistence of window size, position, aspect ratio enforcement state, transparency, and customized keyboard shortcuts in a JSON or INI config file,
- Automatic saving on window move, resize, or close,
- Default window transparency set at 0.9 opacity (10% transparent) with live adjustable transparency slider in settings tab,
- Settings tab includes toggles to enable/disable window snapping to screen edges and other application windows separately,
- Window snapping functionality for both screen edges and other app windows, configurable from settings,
- Keyboard shortcuts including Ctrl+S (Save) and Ctrl+Q (Quit) with facility for user customization via a settings tab button that listens for user key configurations; all shortcuts to be persistent,
- Proper window focus management,
- High DPI and display scaling compatibility,
- Sustained rendering performance at 60+ FPS,
- Targeted tests on Windows OS to verify multi-DPI support, persistence across app restarts, and correct input handling when changing transparency,
- Update README.md reflecting all new UI features, usage, and keyboard shortcut customization instructions.

[EXAMPLES]
- User drags window edges or corners and resizes window;
- User toggles aspect ratio enforcement on/off in settings and resizing follows;
- User adjusts transparency slider sees immediate visual update;
- User configures shortcut keys via listening button and new shortcuts function appropriately;
- Window snaps to screen edges and other apps if toggles enabled, otherwise not;
- Settings persist and restore after app restart.

[DATABASE CONTEXT]
- No database involved; all data persisted locally in settings configuration file.

[DEFINITION OF DONE / CONSTRAINTS]
- Complete implementation of specified window container with title bar and resizing/draggable features
- Fully operational UI controls with event/states handling
- Fully functional customizable keyboard shortcuts with persistence
- Settings tab supports toggles for aspect ratio and snapping configurations
- Window snapping behaves according to user settings
- Transparency adjustable live with persistence
- High DPI compatibility ensured
- Performed end-to-end tests on Windows OS environments with various DPI settings
- Persistence tested for window geometry, transparency, and user shortcuts
- Update README.md with comprehensive UI and feature documentation

# EXECUTION NOTES (AI-DLC)
- Confirm feasibility of Windows borderless window with title bar and required controls using Python ImGui approach.
- Design configuration management system for all persistent settings.
- Implement keyboard shortcut capture and customization UI.
- Integrate snapping with adjustable toggles.
- Validate smooth tab transition animations.
- Ensure robust save/load cycle for settings with graceful failure recovery.
- Persist task progress and document plan in README.md before implementation.
- After confirming this plan, proceed with coding and testing phases.

------------

UI Layout Structure:
1. Top Section (Container Frame):
- Label and text input field for sentence length formatted as 00:00:00
- Must include proper time validation and formatting

2. Middle Section (Container Frame):
- Output calculations displayed in this order:
a) Time > Merits conversion
b) Small visual separator
c) AUEC value of merits (using conversion rate from settings)
d) Small visual separator
e) Fee percentage calculation (using rate from settings for player transfers)

3. Bottom Section (Container Frame):
- Functional buttons for:
* Copy report to clipboard (must include all calculation results)
* Save report to .txt file (with proper file dialog and formatting)
* Clear all inputs and outputs

Visual Design Requirements:
- Remove all unsolicited UI elements (including discount percentage display)
- Increase font sizes and element dimensions for better readability
- Implement professional, visually appealing design with:
* Consistent spacing and alignment
* Appropriate color scheme
* Clear visual hierarchy
* Proper container borders and separators

Functional Requirements:
- Fix all broken UI functionality including:
* Taskbar controls (minimize/exit buttons)
* Window snapping behavior
* Interactive elements (buttons, text inputs)
* System tray functionality

Implementation Standards:
- Ensure end-to-end functionality of all features
- Rigorous testing required for:
* Input validation
* Calculation accuracy
* UI responsiveness
* Cross-feature integration
- Code must be clean, well-commented, and maintainable

Performance Requirements:
- Smooth UI interactions with no lag
- Immediate response to user inputs
- Proper error handling for all operations