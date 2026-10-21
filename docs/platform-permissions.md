# Platform permissions

## macOS

VoiceBridge needs **Microphone** permission to record. The current MVP does not simulate paste or register a system-wide hotkey by default. Future global shortcut and GUI-input adapters will require the appropriate macOS Input Monitoring and/or Accessibility permission; the app must explain why before asking for either.

Run the application from a signed/notarized package for distribution. Development builds may be blocked by Gatekeeper and must be explicitly approved by the user.

## Windows

Microphone access is controlled by Windows Privacy settings. Future global hotkey, focus, and GUI-input support may fail when the target app has a higher integrity level (for example, administrator mode); VoiceBridge must not silently escalate or bypass UAC.

## Linux

Linux is an interface-only target in v0.1. X11 and Wayland differ materially in their input-capture and synthetic-input policies, so no generic compatibility claim is made.
