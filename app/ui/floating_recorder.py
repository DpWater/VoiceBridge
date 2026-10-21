from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class FloatingRecorder(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self.label = QLabel("● 正在录音 00:00")
        self.label.setObjectName("sectionTitle")
        self.level = QProgressBar(); self.level.setRange(0, 100); self.level.setValue(0)
        layout.addWidget(self.label); layout.addWidget(self.level)
        self._seconds = 0
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick)

    def show_recording(self) -> None:
        self._seconds = 0; self._timer.start(1000); self.show()

    def show_status(self, text: str) -> None:
        self._timer.stop(); self.label.setText(text); self.show()

    def _tick(self) -> None:
        self._seconds += 1
        self.label.setText(f"● 正在录音 {self._seconds // 60:02d}:{self._seconds % 60:02d}")
