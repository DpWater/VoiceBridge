from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.theme import APP_STYLE


def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("VoiceBridge")
    application.setQuitOnLastWindowClosed(False)
    application.setStyleSheet(APP_STYLE)
    window = MainWindow(); window.resize(500, 180); window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
