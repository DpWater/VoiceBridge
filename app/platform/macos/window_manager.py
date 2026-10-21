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
        '  return name of first application process whose frontmost is true\n'
        'end tell'
    )
    _paste_script = 'tell application "System Events" to keystroke "v" using command down'

    def __init__(self, runner=subprocess.run) -> None:
        self._runner = runner

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
        app_name = result.stdout.strip() if result.returncode == 0 else ""
        return TargetSnapshot(application_name=app_name or None)

    def activate(self, target: TargetSnapshot) -> bool:
        if not self.is_supported() or not target.application_name:
            return False
        result = self._runner(
            ["/usr/bin/open", "-a", target.application_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            return False
        time.sleep(0.2)
        return self.capture_active_target().application_name == target.application_name

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
