from __future__ import annotations

from collections.abc import Callable
from threading import Event, Thread
from typing import ClassVar


class MacOSReturnKeyInterceptor:
    """Consumes Return only while VoiceBridge records, so it never submits the target chat."""

    _RETURN_KEYCODES: ClassVar[frozenset[int]] = frozenset({36, 76})

    def __init__(self, should_consume: Callable[[], bool], on_return: Callable[[], None]) -> None:
        self.should_consume = should_consume
        self.on_return = on_return
        self._thread: Thread | None = None
        self._started = Event()
        self._error: Exception | None = None
        self._run_loop = None
        self._tap = None

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
        from Quartz import CGEventGetIntegerValueField, kCGEventKeyDown, kCGKeyboardEventKeycode

        if event_type == kCGEventKeyDown and self.should_consume():
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            if keycode in self._RETURN_KEYCODES:
                self.on_return()
                return None
        return event
