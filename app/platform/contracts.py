"""Platform seams. Implementations must state which permission they require."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.contracts import TargetSnapshot


class ClipboardBackend(ABC):
    @abstractmethod
    def copy(self, text: str) -> None: ...


class WindowManager(ABC):
    @abstractmethod
    def capture_active_target(self) -> TargetSnapshot: ...

    @abstractmethod
    def activate(self, target: TargetSnapshot) -> bool: ...


class HotkeyBackend(ABC):
    """A backend must report unavailable instead of silently intercepting input."""
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...
