from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

from app.models.contracts import TargetSnapshot
from app.providers.base import TargetAdapter


class ReviewDialog(QDialog):
    def __init__(
        self,
        original: str,
        revised: str,
        targets: dict[str, TargetAdapter],
        selected_target_id: str,
        snapshot: TargetSnapshot,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("VoiceBridge — Review instruction")
        self.setMinimumSize(620, 360)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Review the instruction and target before sending. Enter dispatches; Shift+Enter adds a line."))
        layout.addWidget(QLabel("Send target"))
        self.target_selector = QComboBox()
        for target_id, target in targets.items():
            self.target_selector.addItem(target.display_name, target_id)
        index = self.target_selector.findData(selected_target_id)
        self.target_selector.setCurrentIndex(max(index, 0))
        layout.addWidget(self.target_selector)
        self.target_status = QLabel()
        self.target_status.setWordWrap(True)
        layout.addWidget(self.target_status)
        self.context_preview = QPlainTextEdit()
        self.context_preview.setReadOnly(True)
        self.context_preview.setMaximumBlockCount(20)
        self.context_preview.setFixedHeight(76)
        layout.addWidget(QLabel("Current conversation preview"))
        layout.addWidget(self.context_preview)
        self._targets = targets
        self._snapshot = snapshot
        self.target_selector.currentIndexChanged.connect(self._target_changed)
        self._target_changed()
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

    @property
    def target(self) -> TargetAdapter:
        return self._targets[self.target_selector.currentData()]

    def _target_changed(self) -> None:
        target = self.target
        conversations = target.discover_conversations()
        if conversations:
            lines = [f"{item.title}\n{chr(10).join(item.preview) or 'No preview provided by target.'}" for item in conversations]
            self.context_preview.setPlainText("\n\n".join(lines))
            self.target_status.setText("Target exposes resumable CLI sessions. Selectable session UI is the next adapter step.")
            return
        app = self._snapshot.application_name or "no pre-recorded application"
        self.context_preview.setPlainText(
            "No chat history is available through this target.\n\n"
            "VoiceBridge will not scrape private desktop conversations. For GUI tools it can only paste into the "
            "verified application that was active before recording."
        )
        self.target_status.setText(f"Recorded active application: {app}")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.accept()
            return
        super().keyPressEvent(event)
