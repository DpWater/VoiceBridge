from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTray:
    def __init__(self, parent, show_window, start_recording, quit_app) -> None:
        self.icon = QSystemTrayIcon(QIcon(), parent)
        menu = QMenu(parent)
        show_action = QAction("显示 VoiceBridge", menu); show_action.triggered.connect(show_window)
        record_action = QAction("开始录音", menu); record_action.triggered.connect(start_recording)
        quit_action = QAction("退出", menu); quit_action.triggered.connect(quit_app)
        menu.addActions([show_action, record_action]); menu.addSeparator(); menu.addAction(quit_action)
        self.icon.setContextMenu(menu)
        self.icon.setToolTip("VoiceBridge")
        self.icon.show()

    def notify(self, title: str, message: str) -> None:
        self.icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4000)
