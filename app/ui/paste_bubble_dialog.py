from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout


class _PasteTextEdit(QTextEdit):
    confirm_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.confirm_requested.emit()
            return
        super().keyPressEvent(event)


class PasteBubbleDialog(QDialog):
    """A small, editable result bubble that returns its text on Enter."""

    def __init__(self, text: str, application_name: str | None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("VoiceBridge — 确认粘贴")
        self.setMinimumWidth(620)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        title = QLabel("刚刚识别到的文字")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        destination = application_name or "原来的光标位置"
        hint = QLabel(f"可以直接修改。按 Enter 粘贴回 {destination}；Shift + Enter 换行。")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.editor = _PasteTextEdit(text)
        self.editor.setMinimumHeight(145)
        self.editor.setPlaceholderText("未识别到文字")
        self.editor.confirm_requested.connect(self._confirm)
        layout.addWidget(self.editor)

        actions = QHBoxLayout()
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        self.paste_button = QPushButton("粘贴到原光标处  ↵")
        self.paste_button.setObjectName("primary")
        self.paste_button.setDefault(True)
        self.paste_button.clicked.connect(self._confirm)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(self.paste_button)
        layout.addLayout(actions)
        self.editor.setFocus()

    @property
    def text(self) -> str:
        return self.editor.toPlainText().strip()

    def _confirm(self) -> None:
        if self.text:
            self.accept()
