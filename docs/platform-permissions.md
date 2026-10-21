# Platform permissions

## macOS

VoiceBridge needs **Microphone** permission to record. GUI paste is disabled by default. When a user explicitly enables it, VoiceBridge needs **Accessibility** permission to restore the application that was active before recording and paste text with Command-V. It never presses Enter automatically.

The GUI adapter does not scrape another application's private conversation content. Cursor, Trae, and other desktop chat applications must expose a stable, user-authorized API before their existing GUI history can be displayed or selected reliably. CLI sessions are a different capability from desktop GUI conversations.

Run the application from a signed/notarized package for distribution. Development builds may be blocked by Gatekeeper and must be explicitly approved by the user.

## Windows

Microphone access is controlled by Windows Privacy settings. Future global hotkey, focus, and GUI-input support may fail when the target app has a higher integrity level (for example, administrator mode); VoiceBridge must not silently escalate or bypass UAC.

## Linux

Linux is an interface-only target in v0.1. X11 and Wayland differ materially in their input-capture and synthetic-input policies, so no generic compatibility claim is made.
