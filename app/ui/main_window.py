from __future__ import annotations

from PySide6.QtCore import QObject, Signal
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
from app.providers.asr.faster_whisper import FasterWhisperProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider
from app.providers.targets.clipboard import ClipboardTargetAdapter
from app.services.audio_recorder import AudioRecorder
from app.services.workflow_controller import WorkflowController
from app.ui.floating_recorder import FloatingRecorder
from app.ui.review_dialog import ReviewDialog
from app.ui.system_tray import SystemTray


class _Signals(QObject):
    review_ready = Signal(str, str)
    failed = Signal(str)


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
        self.signals = _Signals(); self.signals.review_ready.connect(self._review); self.signals.failed.connect(self._error)
        self.floating = FloatingRecorder()
        self.setWindowTitle("VoiceBridge")
        body = QWidget(); layout = QVBoxLayout(body)
        layout.addWidget(QLabel("Local-first voice commands for coding agents"))
        self.status = QLabel("Ready. Click Record, then Stop to review before copying.")
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self._toggle_recording)
        layout.addWidget(self.status); layout.addWidget(self.record_button); self.setCentralWidget(body)
        self.tray = SystemTray(self, self._show_from_tray, self._start_from_tray, QApplication.quit)

    def _show_from_tray(self) -> None:
        self.showNormal(); self.raise_(); self.activateWindow()

    def _start_from_tray(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            self._toggle_recording()

    def _toggle_recording(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            try:
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
        dialog = ReviewDialog(original, revised, self)
        if dialog.exec() and dialog.text:
            try:
                self.controller.workflow.transition(WorkflowState.DISPATCHING)
                result = ClipboardTargetAdapter().dispatch(dialog.text)
                self.controller.workflow.transition(WorkflowState.COMPLETED)
                self.status.setText(result.message)
            except Exception as exc:
                self._error(str(exc)); return
        else:
            self.controller.cancel()
        self._finish()

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
        self.recorder.cancel(); self.controller.shutdown(); super().closeEvent(event)
