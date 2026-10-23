from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from app.models.contracts import TargetSnapshot


class FloatingRecorder(QFrame):
    """Small, non-activating feedback placed next to the captured cursor."""
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("floatingFeedback")
        self.setFixedWidth(350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)
        row = QHBoxLayout()
        row.setSpacing(9)
        self.icon = QLabel("●")
        self.icon.setObjectName("feedbackIcon")
        self.label = QLabel("正在听你说话")
        self.label.setObjectName("feedbackTitle")
        self.elapsed = QLabel("00:00")
        self.elapsed.setObjectName("feedbackElapsed")
        row.addWidget(self.icon); row.addWidget(self.label); row.addStretch(); row.addWidget(self.elapsed)
        self.detail = QLabel("声音正在采集 · 按 Enter 结束")
        self.detail.setObjectName("feedbackDetail")
        self.level = QProgressBar()
        self.level.setObjectName("feedbackProgress")
        self.level.setRange(0, 0)
        layout.addLayout(row); layout.addWidget(self.detail); layout.addWidget(self.level)
        self._seconds = 0
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick)

    def show_recording(self, target: TargetSnapshot) -> None:
        self._seconds = 0
        self.icon.setText("●")
        self.label.setText("正在听你说话")
        self.detail.setText("声音正在采集 · 按 Enter 结束")
        self.elapsed.show()
        self.level.show()
        self._timer.start(1000)
        self._show_near(target)

    def show_status(self, text: str, target: TargetSnapshot) -> None:
        self._seconds = 0
        self.icon.setText("◌")
        self.label.setText(text)
        self.detail.setText("本地语音识别完成后，将由 DeepSeek 整理表达")
        self.elapsed.setText("00:00")
        self.elapsed.show()
        self.level.show()
        self._timer.start(1000)
        self._show_near(target)

    def show_confirmation(self, target: TargetSnapshot) -> None:
        self._timer.stop()
        self.icon.setText("✓")
        self.label.setText("已粘贴到光标处")
        self.detail.setText("未自动提交，你仍可继续编辑后再发送")
        self.elapsed.hide()
        self.level.hide()
        self._show_near(target)
        QTimer.singleShot(2600, self.hide)

    def _show_near(self, target: TargetSnapshot) -> None:
        self.adjustSize()
        point = self._anchor(target)
        screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
        if screen is None:
            self.move(point)
        else:
            bounds = screen.availableGeometry()
            x = max(bounds.left() + 10, min(point.x() - self.width() + 26, bounds.right() - self.width() - 10))
            y = point.y() - self.height() - 18
            if y < bounds.top() + 10:
                y = min(point.y() + 18, bounds.bottom() - self.height() - 10)
            self.move(x, y)
        self.show()
        self.raise_()

    @staticmethod
    def _anchor(target: TargetSnapshot):
        if target.cursor_x is not None and target.cursor_y is not None:
            from PySide6.QtCore import QPoint

            return QPoint(target.cursor_x, target.cursor_y)
        return QCursor.pos()

    def _tick(self) -> None:
        self._seconds += 1
        self.elapsed.setText(f"{self._seconds // 60:02d}:{self._seconds % 60:02d}")
