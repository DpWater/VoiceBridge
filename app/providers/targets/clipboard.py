from __future__ import annotations

from app.models.contracts import DispatchResult
from app.providers.base import TargetAdapter


class ClipboardTargetAdapter(TargetAdapter):
    target_id = "clipboard"

    def dispatch(self, text: str) -> DispatchResult:
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        return DispatchResult("copied", "Text copied to clipboard. Paste it into the selected target.")
