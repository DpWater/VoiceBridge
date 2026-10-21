from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.secrets import SecretStore
from app.config.store import SettingsStore
from app.core.state_machine import WorkflowState
from app.models.contracts import AppSettings
from app.platform.factory import get_window_manager
from app.providers.asr.faster_whisper import FasterWhisperProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider
from app.providers.targets.clipboard import ClipboardTargetAdapter
from app.providers.targets.gui_input import GuiInputTargetAdapter
from app.services.audio_recorder import AudioRecorder
from app.services.hotkey import PynputToggleHotkey
from app.services.workflow_controller import WorkflowController
from app.ui.floating_recorder import FloatingRecorder
from app.ui.review_dialog import ReviewDialog
from app.ui.shortcut_settings_dialog import ShortcutSettingsDialog
from app.ui.system_tray import SystemTray


class _Signals(QObject):
    review_ready = Signal(str, str)
    failed = Signal(str)
    hotkey_pressed = Signal()


class MainWindow(QMainWindow):
    def __init__(self, store: SettingsStore | None = None) -> None:
        super().__init__()
        self.store = store or SettingsStore()
        self.settings: AppSettings = self.store.load()
        self.recorder = AudioRecorder(max_seconds=self.settings.max_recording_seconds)
        asr = FasterWhisperProvider(self.settings.asr_model, self.settings.asr_device,
                                    self.settings.asr_compute_type, self.settings.language)
        key = SecretStore().get_api_key()
        llm = (
            OpenAICompatibleProvider(self.settings.llm_base_url, key, self.settings.llm_model,
                                     self.settings.llm_timeout_seconds)
            if self.settings.use_enhancement and key
            else None
        )
        self.controller = WorkflowController(asr, llm)
        self.window_manager = get_window_manager()
        self.target_snapshot = self.window_manager.capture_active_target()
        self.signals = _Signals()
        self.signals.review_ready.connect(self._review)
        self.signals.failed.connect(self._error)
        self.signals.hotkey_pressed.connect(self._on_hotkey)
        self.floating = FloatingRecorder()
        self.setWindowTitle("VoiceBridge")
        body = QWidget(); layout = QVBoxLayout(body)
        layout.addWidget(QLabel("Local-first voice commands for coding agents"))
        self.status = QLabel("Ready. Click Record, then Stop to review before copying.")
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self._toggle_recording)
        self.shortcut_button = QPushButton("Shortcut settings…")
        self.shortcut_button.clicked.connect(self._configure_shortcut)
        layout.addWidget(self.status)
        layout.addWidget(self.record_button)
        layout.addWidget(self.shortcut_button)
        self.setCentralWidget(body)
        self.tray = SystemTray(self, self._show_from_tray, self._start_from_tray, QApplication.quit)
        self.hotkey_backend = None
        if self.settings.hotkey_enabled:
            self._start_hotkey()

    def _show_from_tray(self) -> None:
        self.showNormal(); self.raise_(); self.activateWindow()

    def _start_from_tray(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            self._toggle_recording()

    def _on_hotkey(self) -> None:
        if self.controller.workflow.state in {WorkflowState.IDLE, WorkflowState.RECORDING}:
            self._toggle_recording()

    def _start_hotkey(self) -> None:
        try:
            self.hotkey_backend = PynputToggleHotkey(
                self.settings.hotkey, lambda: self.signals.hotkey_pressed.emit()
            )
            self.hotkey_backend.start()
            self.status.setText(f"Global shortcut enabled: {self.settings.hotkey}")
        except RuntimeError as exc:
            self.hotkey_backend = None
            self.status.setText(f"Global shortcut unavailable: {exc}")

    def _configure_shortcut(self) -> None:
        dialog = ShortcutSettingsDialog(self.settings.hotkey, self.settings.hotkey_enabled, self)
        if not dialog.exec():
            return
        if self.hotkey_backend:
            self.hotkey_backend.stop()
            self.hotkey_backend = None
        self.settings.hotkey = dialog.hotkey
        self.settings.hotkey_enabled = dialog.enabled.isChecked()
        self.store.save(self.settings)
        if self.settings.hotkey_enabled:
            self._start_hotkey()
        else:
            self.status.setText("Global shortcut disabled")

    def _toggle_recording(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            try:
                self.target_snapshot = self.window_manager.capture_active_target()
                self.controller.workflow.start(); self.recorder.start()
                self.record_button.setText("Stop and transcribe"); self.status.setText("Recording…")
                self.floating.show_recording()
            except Exception as exc:
                self._error(str(exc))
        elif self.controller.workflow.state is WorkflowState.RECORDING:
            try:
                audio = self.recorder.stop(); self.record_button.setEnabled(False)
                self.status.setText("Transcribing…"); self.floating.show_status("Transcribing…")
                self.controller.process(audio, self.settings.terminology,
                                        lambda raw, revised: self.signals.review_ready.emit(raw, revised),
                                        lambda message: self.signals.failed.emit(message), self.settings.use_enhancement)
            except Exception as exc:
                self._error(str(exc))

    def _review(self, original: str, revised: str) -> None:
        self.floating.hide(); self.status.setText("Waiting for your review")
        dialog = ReviewDialog(
            original,
            revised,
            self._build_targets(),
            self.settings.default_target,
            self.target_snapshot,
            self,
        )
        if dialog.exec() and dialog.text:
            try:
                self.controller.workflow.transition(WorkflowState.DISPATCHING)
                result = dialog.target.dispatch(dialog.text)
                self.controller.workflow.transition(WorkflowState.COMPLETED)
                self.status.setText(result.message)
            except Exception as exc:
                self._error(str(exc)); return
        else:
            self.controller.cancel()
        self._finish()

    def _copy_to_clipboard(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)

    @staticmethod
    def _clipboard_text() -> str:
        return QGuiApplication.clipboard().text()

    @staticmethod
    def _schedule(delay_ms: int, callback) -> None:
        QTimer.singleShot(delay_ms, callback)

    def _build_targets(self):
        return {
            "clipboard": ClipboardTargetAdapter(),
            "cursor-current": GuiInputTargetAdapter(
                "cursor-current",
                "Cursor — recorded right-side chat input",
                "Cursor",
                self.target_snapshot,
                self.window_manager,
                self._copy_to_clipboard,
                self._clipboard_text,
                self._schedule,
                self.settings.gui_paste_enabled,
            ),
            "trae-current": GuiInputTargetAdapter(
                "trae-current",
                "Trae — recorded right-side chat input",
                "Trae",
                self.target_snapshot,
                self.window_manager,
                self._copy_to_clipboard,
                self._clipboard_text,
                self._schedule,
                self.settings.gui_paste_enabled,
            ),
        }

    def _error(self, message: str) -> None:
        self.floating.hide(); self.status.setText(f"Error: {message}")
        QMessageBox.warning(self, "VoiceBridge", message)
        if self.controller.workflow.state not in {WorkflowState.IDLE, WorkflowState.FAILED}:
            self.controller.cancel()
        self._finish()

    def _finish(self) -> None:
        self.record_button.setEnabled(True); self.record_button.setText("Record")
        if self.controller.workflow.state in {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED}:
            self.controller.workflow.reset()

    def closeEvent(self, event) -> None:
        self.recorder.cancel()
        if self.hotkey_backend:
            self.hotkey_backend.stop()
        self.controller.shutdown()
        super().closeEvent(event)
