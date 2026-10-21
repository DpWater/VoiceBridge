from __future__ import annotations

from collections.abc import Callable

from app.platform.contracts import HotkeyBackend


class PynputToggleHotkey(HotkeyBackend):
    """Global chord backend for the optional toggle mode.

    Push-to-talk is intentionally not enabled through this class: on macOS it
    requires Input Monitoring / Accessibility consent and needs a separate
    key-release implementation. The main window remains usable without it.
    """
    def __init__(self, chord: str, on_activate: Callable[[], None]) -> None:
        self.chord = chord
        self.on_activate = on_activate
        self._listener = None

    def start(self) -> None:
        try:
            from pynput import keyboard
        except ImportError as exc:
            raise RuntimeError("pynput is not installed; global hotkeys are unavailable") from exc
        try:
            self._listener = keyboard.GlobalHotKeys({self.chord: self.on_activate})
            self._listener.start()
        except Exception as exc:
            raise RuntimeError(f"Could not register global hotkey {self.chord}: {exc}") from exc

    def stop(self) -> None:
        if self._listener:
            self._listener.stop(); self._listener = None
