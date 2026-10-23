from __future__ import annotations

import platform
import subprocess
import time

from app.models.contracts import TargetSnapshot


class MacOSWindowManager:
    """Small macOS implementation with fixed AppleScript only.

    Pasting requires Accessibility permission. We intentionally do not inspect
    another application's UI tree or attempt to infer private chat history.
    """

    _frontmost_script = (
        'tell application "System Events"\n'
        '  set targetProcess to first application process whose frontmost is true\n'
        '  return (name of targetProcess) & "|" & (unix id of targetProcess)\n'
        'end tell'
    )
    _paste_script = 'tell application "System Events" to keystroke "v" using command down'

    def __init__(self, runner=subprocess.run, cursor_position=None) -> None:
        self._runner = runner
        self._cursor_position = cursor_position or self._read_cursor_position

    @staticmethod
    def is_supported() -> bool:
        return platform.system() == "Darwin"

    def capture_active_target(self) -> TargetSnapshot:
        if not self.is_supported():
            return TargetSnapshot()
        result = self._runner(
            ["/usr/bin/osascript", "-e", self._frontmost_script],
            capture_output=True,
            text=True,
            check=False,
        )
        app_name, process_id = self._parse_frontmost(result.stdout if result.returncode == 0 else "")
        cursor_x, cursor_y = self._cursor_position()
        return TargetSnapshot(
            application_name=app_name or None,
            process_id=process_id,
            cursor_x=cursor_x,
            cursor_y=cursor_y,
        )

    @staticmethod
    def _parse_frontmost(output: str) -> tuple[str, int | None]:
        name, separator, possible_pid = output.strip().rpartition("|")
        if separator and possible_pid.isdigit():
            return name, int(possible_pid)
        return output.strip(), None

    @staticmethod
    def _read_cursor_position() -> tuple[int | None, int | None]:
        """Read the pointer location without inspecting the target application's UI."""
        try:
            from Quartz import CGEventCreate, CGEventGetLocation

            point = CGEventGetLocation(CGEventCreate(None))
            return round(point.x), round(point.y)
        except Exception:  # noqa: BLE001 - cursor anchoring is an optional visual enhancement.
            return None, None

    def activate(self, target: TargetSnapshot) -> bool:
        if not self.is_supported() or not target.application_name:
            return False
        if target.process_id:
            result = self._runner(
                [
                    "/usr/bin/osascript",
                    "-e",
                    (
                        'tell application "System Events" to set frontmost of first application process '
                        f"whose unix id is {target.process_id} to true"
                    ),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                time.sleep(0.25)
                if self.capture_active_target().process_id == target.process_id:
                    return True
        result = self._runner(
            ["/usr/bin/open", "-a", target.application_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            return False
        time.sleep(0.2)
        restored = self.capture_active_target()
        return restored.application_name == target.application_name

    def paste(self) -> bool:
        if not self.is_supported():
            return False
        result = self._runner(
            ["/usr/bin/osascript", "-e", self._paste_script],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
