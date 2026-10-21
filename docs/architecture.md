# Architecture

VoiceBridge adopts Python 3.11+ and PySide6. It is a local desktop application; it has no service-side dependency.

```text
PySide6 UI / tray / review dialog
          │ (events only)
WorkflowController ─── AudioRecorder
          │                   │
Provider contracts ─ ASR / LLM / target adapters
          │
SettingsStore + OS keychain + optional local history
```

The UI never imports a concrete ASR or LLM implementation except in the composition root (`MainWindow`). Providers return immutable result contracts. The workflow controller serializes model work on one worker so a later recording cannot be overwritten by an earlier response.

The MVP dispatches only to the clipboard. GUI paste automation is deliberately deferred: target-window identity and macOS accessibility permissions must be implemented and manually tested before any synthetic paste action is enabled.
