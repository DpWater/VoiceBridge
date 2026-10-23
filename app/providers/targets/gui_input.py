from __future__ import annotations

from collections.abc import Callable

from app.models.contracts import DispatchResult, TargetSnapshot
from app.providers.base import TargetAdapter


class GuiInputTargetAdapter(TargetAdapter):
    """Paste into the chat input that had focus in the recorded application.

    No click coordinates are used: the user chooses the right-side chat input
    before starting. This avoids accidentally focusing the code editor.
    """

    def __init__(
        self,
        target_id: str,
        display_name: str,
        expected_application: str | None,
        snapshot: TargetSnapshot,
        window_manager,
        copy_text: Callable[[str], None],
        read_text: Callable[[], str],
        schedule: Callable[[int, Callable[[], None]], None],
        paste_enabled: bool,
    ) -> None:
        self.target_id = target_id
        self._display_name = display_name
        self.expected_application = expected_application
        self.snapshot = snapshot
        self.window_manager = window_manager
        self.copy_text = copy_text
        self.read_text = read_text
        self.schedule = schedule
        self.paste_enabled = paste_enabled

    @property
    def display_name(self) -> str:
        return self._display_name

    def dispatch(self, text: str) -> DispatchResult:
        if not self.paste_enabled:
            raise RuntimeError("GUI paste is disabled. Enable it explicitly in VoiceBridge settings first.")
        actual = self.snapshot.application_name
        if self.expected_application and actual != self.expected_application:
            raise RuntimeError(
                f"The recorded target is {actual or 'unknown'}, not {self.expected_application}. "
                "Focus the intended right-side chat input before starting the recording."
            )
        if not self.window_manager.activate(self.snapshot):
            raise RuntimeError("Could not restore the recorded target window.")
        previous_text = self.read_text()
        self.copy_text(text)
        if not self.window_manager.paste():
            raise RuntimeError("Paste failed. Grant VoiceBridge Accessibility permission, then retry.")
        self.schedule(250, lambda: self._restore_clipboard_if_unchanged(text, previous_text))
        destination = self.expected_application or actual or "recorded application"
        return DispatchResult(
            "input",
            f"Paste shortcut sent to the recorded {destination} window; verify it before submitting.",
        )

    def _restore_clipboard_if_unchanged(self, temporary_text: str, previous_text: str) -> None:
        """Never replace a newer user copy operation with a stale clipboard value."""
        if self.read_text() == temporary_text:
            self.copy_text(previous_text)
