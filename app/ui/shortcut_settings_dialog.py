from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QKeySequenceEdit,
    QLabel,
    QVBoxLayout,
)

from app.services.hotkey import to_pynput_hotkey, to_qt_portable_text


class ShortcutSettingsDialog(QDialog):
    def __init__(self, hotkey: str, enabled: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("VoiceBridge — Shortcut settings")
        self.setMinimumWidth(410)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Press your preferred shortcut. Use at least one modifier key."))
        self.editor = QKeySequenceEdit()
        self.editor.setKeySequence(QKeySequence.fromString(to_qt_portable_text(hotkey), QKeySequence.SequenceFormat.PortableText))
        layout.addWidget(self.editor)
        self.enabled = QCheckBox("Enable global shortcut")
        self.enabled.setChecked(enabled)
        layout.addWidget(self.enabled)
        self.error = QLabel()
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def hotkey(self) -> str:
        text = self.editor.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        return to_pynput_hotkey(text)

    def _save(self) -> None:
        try:
            _ = self.hotkey
        except ValueError as exc:
            self.error.setText(str(exc))
            return
        self.accept()
