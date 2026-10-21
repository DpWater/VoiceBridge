# Architecture decisions

## ADR-001: Python + PySide6 (accepted)

We chose the proposed Python 3.11 / PySide6 route rather than Tauri plus a Python sidecar. `faster-whisper`, audio capture, and provider configuration can run in a single process; this reduces IPC, packaging and permission surface for the MVP. PySide6 supports macOS and Windows. The trade-off is a larger installer than a pure native shell and platform-specific testing is still required.

## ADR-002: clipboard is the only automatic delivery in v0.1 (accepted)

Copying is reliable and reversible. Simulating a paste or Enter into an application requires verified foreground-window handling and platform accessibility permissions. Claiming that a key event equals successful delivery would be unsafe, so GUI input remains a separately tested adapter.

## ADR-003: API keys use the OS credential store (accepted)

Settings are JSON and exclude secrets. Keyring failures are surfaced as configuration errors; keys are never written into logs or the project configuration.
