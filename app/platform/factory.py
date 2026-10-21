from __future__ import annotations

from app.models.contracts import TargetSnapshot
from app.platform.macos.window_manager import MacOSWindowManager


class UnsupportedWindowManager:
    def capture_active_target(self) -> TargetSnapshot:
        return TargetSnapshot()

    def activate(self, target: TargetSnapshot) -> bool:
        return False

    def paste(self) -> bool:
        return False


def get_window_manager() -> MacOSWindowManager | UnsupportedWindowManager:
    return MacOSWindowManager() if MacOSWindowManager.is_supported() else UnsupportedWindowManager()
