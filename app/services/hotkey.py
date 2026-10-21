from __future__ import annotations

from collections.abc import Callable

from app.platform.contracts import HotkeyBackend

_QT_TO_PYNPUT = {
    "meta": "<cmd>",
    "ctrl": "<ctrl>",
    "shift": "<shift>",
    "alt": "<alt>",
    "space": "<space>",
    "escape": "<esc>",
    "esc": "<esc>",
    "return": "<enter>",
    "enter": "<enter>",
    "tab": "<tab>",
}
_PYNPUT_TO_QT = {value: key.title() for key, value in _QT_TO_PYNPUT.items()}
_PYNPUT_TO_QT["<cmd>"] = "Meta"
_PYNPUT_TO_QT["<ctrl>"] = "Ctrl"


def to_pynput_hotkey(qt_portable_text: str) -> str:
    """Convert QKeySequence PortableText to pynput's GlobalHotKeys grammar."""
    if not qt_portable_text.strip():
        raise ValueError("Choose a shortcut first")
    result: list[str] = []
    for token in qt_portable_text.split("+"):
        item = token.strip()
        lowered = item.lower()
        if lowered in _QT_TO_PYNPUT:
            result.append(_QT_TO_PYNPUT[lowered])
        elif len(item) == 1 and item.isprintable():
            result.append(item.lower())
        elif lowered.startswith("f") and lowered[1:].isdigit():
            result.append(f"<{lowered}>")
        else:
            raise ValueError(f"Unsupported shortcut key: {item}")
    if len(result) < 2:
        raise ValueError("Use a key together with at least one modifier")
    return "+".join(result)


def to_qt_portable_text(pynput_hotkey: str) -> str:
    """Convert stored pynput grammar to QKeySequence PortableText."""
    result: list[str] = []
    for token in pynput_hotkey.split("+"):
        item = token.strip().lower()
        if item in _PYNPUT_TO_QT:
            result.append(_PYNPUT_TO_QT[item])
        elif item.startswith("<f") and item.endswith(">"):
            result.append(item[1:-1].upper())
        elif len(item) == 1 and item.isprintable():
            result.append(item.upper())
        else:
            raise ValueError(f"Unsupported saved shortcut key: {token}")
    return "+".join(result)


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
