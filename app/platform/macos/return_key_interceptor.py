from __future__ import annotations

from collections.abc import Callable
from threading import Event, Thread
from typing import ClassVar


class MacOSReturnKeyInterceptor:
    """Uses macOS physical key codes for the global hotkey and recording Return.

    ``pynput`` listens to translated characters on macOS.  That makes a chord
    such as Control+Shift+9 unreliable: the final key is translated to ``(``
    before the listener sees it.  An event tap works with the actual keyboard
    key code, so the shortcut works consistently regardless of Shift.
    """

    _RETURN_KEYCODES: ClassVar[frozenset[int]] = frozenset({36, 76})
    _KEYCODES: ClassVar[dict[str, int]] = {
        "a": 0, "b": 11, "c": 8, "d": 2, "e": 14, "f": 3, "g": 5,
        "h": 4, "i": 34, "j": 38, "k": 40, "l": 37, "m": 46, "n": 45,
        "o": 31, "p": 35, "q": 12, "r": 15, "s": 1, "t": 17, "u": 32,
        "v": 9, "w": 13, "x": 7, "y": 16, "z": 6,
        "0": 29, "1": 18, "2": 19, "3": 20, "4": 21, "5": 23,
        "6": 22, "7": 26, "8": 28, "9": 25,
        "<space>": 49, "<esc>": 53,
        "<f1>": 122, "<f2>": 120, "<f3>": 99, "<f4>": 118,
        "<f5>": 96, "<f6>": 97, "<f7>": 98, "<f8>": 100,
        "<f9>": 101, "<f10>": 109, "<f11>": 103, "<f12>": 111,
    }

    def __init__(
        self,
        hotkey: str,
        on_hotkey: Callable[[], None],
        should_consume_return: Callable[[], bool],
        on_return: Callable[[], None],
    ) -> None:
        self._hotkey_keycode, self._hotkey_modifiers = self._parse_hotkey(hotkey)
        self.on_hotkey = on_hotkey
        self.should_consume_return = should_consume_return
        self.on_return = on_return
        self._thread: Thread | None = None
        self._started = Event()
        self._error: Exception | None = None
        self._run_loop = None
        self._tap = None

    @classmethod
    def _parse_hotkey(cls, hotkey: str) -> tuple[int, int]:
        from Quartz import (
            kCGEventFlagMaskAlternate,
            kCGEventFlagMaskCommand,
            kCGEventFlagMaskControl,
            kCGEventFlagMaskShift,
        )

        modifier_masks = {
            "<cmd>": kCGEventFlagMaskCommand,
            "<ctrl>": kCGEventFlagMaskControl,
            "<shift>": kCGEventFlagMaskShift,
            "<alt>": kCGEventFlagMaskAlternate,
        }
        keycode: int | None = None
        required_modifiers = 0
        for token in (part.strip().lower() for part in hotkey.split("+")):
            if token in modifier_masks:
                required_modifiers |= modifier_masks[token]
            elif token in cls._KEYCODES and keycode is None:
                keycode = cls._KEYCODES[token]
            else:
                raise RuntimeError(f"Unsupported macOS shortcut: {hotkey}")
        if keycode is None or not required_modifiers:
            raise RuntimeError("Choose a shortcut with at least one modifier")
        return keycode, required_modifiers

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._started.clear()
        self._error = None
        self._thread = Thread(target=self._run, name="voicebridge-return-key", daemon=True)
        self._thread.start()
        if not self._started.wait(timeout=1.5):
            raise RuntimeError("Timed out while registering the Return-key interceptor")
        if self._error:
            raise RuntimeError(f"Could not intercept Return: {self._error}") from self._error

    def stop(self) -> None:
        if self._run_loop is not None:
            from Quartz import CFRunLoopStop

            CFRunLoopStop(self._run_loop)
        self._thread = None
        self._run_loop = None
        self._tap = None

    def _run(self) -> None:
        try:
            from Quartz import (
                CFMachPortCreateRunLoopSource,
                CFRunLoopAddSource,
                CFRunLoopGetCurrent,
                CFRunLoopRun,
                CGEventMaskBit,
                CGEventTapCreate,
                CGEventTapEnable,
                kCFRunLoopCommonModes,
                kCGEventKeyDown,
                kCGHeadInsertEventTap,
                kCGSessionEventTap,
            )
            self._tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                0,
                CGEventMaskBit(kCGEventKeyDown),
                self._handle_event,
                None,
            )
            if self._tap is None:
                raise RuntimeError("macOS Input Monitoring permission is required")
            self._run_loop = CFRunLoopGetCurrent()
            source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
            CFRunLoopAddSource(self._run_loop, source, kCFRunLoopCommonModes)
            CGEventTapEnable(self._tap, True)
            self._started.set()
            CFRunLoopRun()
        except Exception as exc:  # noqa: BLE001 - macOS event-tap setup has several PyObjC error types.
            self._error = exc
            self._started.set()

    def _handle_event(self, _proxy, event_type, event, _refcon):
        from Quartz import (
            CGEventGetFlags,
            CGEventGetIntegerValueField,
            kCGEventKeyDown,
            kCGKeyboardEventKeycode,
        )

        if event_type == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            flags = CGEventGetFlags(event)
            if keycode == self._hotkey_keycode and (flags & self._hotkey_modifiers) == self._hotkey_modifiers:
                self.on_hotkey()
                return None
            if self.should_consume_return() and keycode in self._RETURN_KEYCODES:
                self.on_return()
                return None
        return event
