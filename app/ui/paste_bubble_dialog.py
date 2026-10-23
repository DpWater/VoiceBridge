from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.models.contracts import TargetSnapshot


class _PasteTextEdit(QTextEdit):
    confirm_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.confirm_requested.emit()
            return
        super().keyPressEvent(event)


class PasteBubbleDialog(QDialog):
    """A small, editable result bubble that returns its text on Enter."""

    def __init__(self, text: str, target: TargetSnapshot, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("VoiceBridge")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("pasteBubble")
        self.setMinimumWidth(430)
        self.setMaximumWidth(470)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("pasteBubbleCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 11, 12, 10)
        card_layout.setSpacing(8)
        header = QHBoxLayout()
        badge = QLabel("✦")
        badge.setObjectName("pasteBadge")
        title = QLabel("识别结果")
        title.setObjectName("pasteTitle")
        editable = QLabel("可直接编辑")
        editable.setObjectName("pasteEditable")
        header.addWidget(badge); header.addWidget(title); header.addStretch(); header.addWidget(editable)
        card_layout.addLayout(header)
        self.editor = _PasteTextEdit(text)
        self.editor.setMinimumHeight(106)
        self.editor.setMaximumHeight(160)
        self.editor.setPlaceholderText("未识别到文字")
        self.editor.confirm_requested.connect(self._confirm)
        card_layout.addWidget(self.editor)

        actions = QHBoxLayout()
        hint = QLabel("Enter 粘贴  ·  Shift + Enter 换行")
        hint.setObjectName("pasteHint")
        cancel = QPushButton("取消")
        cancel.setObjectName("pasteCancel")
        cancel.clicked.connect(self.reject)
        self.paste_button = QPushButton("粘贴  ↵")
        self.paste_button.setObjectName("primary")
        self.paste_button.setDefault(True)
        self.paste_button.clicked.connect(self._confirm)
        actions.addWidget(hint); actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(self.paste_button)
        card_layout.addLayout(actions)
        layout.addWidget(card)
        self._position_near(target)
        self.editor.setFocus()

    @property
    def text(self) -> str:
        return self.editor.toPlainText().strip()

    def _confirm(self) -> None:
        if self.text:
            self.accept()

    def _position_near(self, target: TargetSnapshot) -> None:
        self.adjustSize()
        anchor = QPoint(target.cursor_x, target.cursor_y) if target.cursor_x is not None and target.cursor_y is not None else QCursor.pos()
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        if screen is None:
            self.move(anchor)
            return
        bounds = screen.availableGeometry()
        x = max(bounds.left() + 10, min(anchor.x() - self.width() + 26, bounds.right() - self.width() - 10))
        y = anchor.y() - self.height() - 18
        if y < bounds.top() + 10:
            y = min(anchor.y() + 18, bounds.bottom() - self.height() - 10)
        self.move(x, y)
