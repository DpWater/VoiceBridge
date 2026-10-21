from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
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
        self.setWindowTitle("VoiceBridge — 确认并发送")
        self.setMinimumSize(1020, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(16)

        eyebrow = QLabel("READY TO ROUTE")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("确认后，发送到正在工作的对话")
        title.setObjectName("headline")
        layout.addWidget(title)
        hint = QLabel("检查语音识别结果，选择目标；VoiceBridge 只会粘贴文字，不会替你自动提交。")
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        instruction_card = QFrame()
        instruction_card.setObjectName("card")
        instruction_layout = QVBoxLayout(instruction_card)
        instruction_layout.setContentsMargins(20, 18, 20, 18)
        instruction_layout.setSpacing(10)
        label = QLabel("准备发送的指令")
        label.setObjectName("sectionTitle")
        instruction_layout.addWidget(label)
        copy_hint = QLabel("Enter 确认发送 · Shift + Enter 换行")
        copy_hint.setObjectName("muted")
        instruction_layout.addWidget(copy_hint)
        tabs = QTabWidget()
        self.editor = QTextEdit(revised)
        self.editor.setPlaceholderText("未识别到文本")
        raw = QTextEdit(original)
        raw.setReadOnly(True)
        tabs.addTab(self.editor, "待发送")
        tabs.addTab(raw, "原始语音识别")
        instruction_layout.addWidget(tabs, 1)
        columns.addWidget(instruction_card, 3)

        route_card = QFrame()
        route_card.setObjectName("routeCard")
        route_layout = QVBoxLayout(route_card)
        route_layout.setContentsMargins(20, 18, 20, 18)
        route_layout.setSpacing(10)
        route_label = QLabel("路由目标")
        route_label.setObjectName("sectionTitle")
        route_layout.addWidget(route_label)
        route_description = QLabel("发送到录音开始前已聚焦的右侧对话输入框")
        route_description.setObjectName("muted")
        route_description.setWordWrap(True)
        route_layout.addWidget(route_description)
        self.target_selector = QComboBox()
        for target_id, target in targets.items():
            self.target_selector.addItem(target.display_name, target_id)
        index = self.target_selector.findData(selected_target_id)
        self.target_selector.setCurrentIndex(max(index, 0))
        route_layout.addWidget(self.target_selector)
        self.target_status = QLabel()
        self.target_status.setObjectName("targetStatus")
        self.target_status.setWordWrap(True)
        route_layout.addWidget(self.target_status)
        capability_title = QLabel("安全边界")
        capability_title.setObjectName("sectionTitle")
        route_layout.addWidget(capability_title)
        capabilities = QHBoxLayout()
        for text in ("右侧输入框", "仅粘贴", "不自动提交"):
            badge = QLabel(text)
            badge.setObjectName("capabilityActive")
            capabilities.addWidget(badge)
        capabilities.addStretch()
        route_layout.addLayout(capabilities)
        context_label = QLabel("当前对话内容")
        context_label.setObjectName("sectionTitle")
        route_layout.addWidget(context_label)
        self.context_preview = QPlainTextEdit()
        self.context_preview.setObjectName("contextCard")
        self.context_preview.setReadOnly(True)
        self.context_preview.setMaximumBlockCount(20)
        self.context_preview.setFixedHeight(180)
        route_layout.addWidget(self.context_preview)
        route_layout.addStretch()
        columns.addWidget(route_card, 2)
        layout.addLayout(columns, 1)

        self._targets = targets
        self._snapshot = snapshot
        self.target_selector.currentIndexChanged.connect(self._target_changed)
        self._target_changed()
        actions = QHBoxLayout()
        actions.addStretch()
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(cancel_button)
        self.copy_button = QPushButton("确认并发送  ↗")
        self.copy_button.setObjectName("primary")
        self.copy_button.setDefault(True)
        self.copy_button.clicked.connect(self.accept)
        actions.addWidget(self.copy_button)
        layout.addLayout(actions)
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
            lines = [f"{item.title}\n{chr(10).join(item.preview) or '该目标未提供预览。'}" for item in conversations]
            self.context_preview.setPlainText("\n\n".join(lines))
            self.target_status.setText("该目标提供了可恢复的 CLI 会话；选择具体会话的界面将在下一步接入。")
            return
        app = self._snapshot.application_name or "未记录到应用"
        self.context_preview.setPlainText(
            "当前目标未开放可读取的对话历史。\n\n"
            "VoiceBridge 不抓取桌面应用的私有聊天内容。对于 GUI 工具，它只会将文本粘贴到录音前已聚焦的右侧对话输入框。"
        )
        self.target_status.setText(
            f"录音前的活动应用：{app}。使用快捷键前，请先聚焦 IDE 右侧的对话输入框。"
        )

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.accept()
            return
        super().keyPressEvent(event)
