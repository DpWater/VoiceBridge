from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)


class ReviewDialog(QDialog):
    def __init__(self, original: str, revised: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("VoiceBridge — Review instruction")
        self.setMinimumSize(620, 360)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Review the instruction before sending. Enter copies it; Shift+Enter adds a line."))
        tabs = QTabWidget()
        self.editor = QTextEdit(revised)
        self.editor.setPlaceholderText("No text was recognized")
        raw = QTextEdit(original); raw.setReadOnly(True)
        tabs.addTab(self.editor, "Ready to send")
        tabs.addTab(raw, "Original ASR")
        layout.addWidget(tabs)
        self.copy_button = QPushButton("Copy")
        self.copy_button.setDefault(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.addButton(self.copy_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.rejected.connect(self.reject)
        self.copy_button.clicked.connect(self.accept)
        layout.addWidget(buttons)
        self.editor.setFocus()

    @property
    def text(self) -> str:
        return self.editor.toPlainText().strip()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.accept()
            return
        super().keyPressEvent(event)
