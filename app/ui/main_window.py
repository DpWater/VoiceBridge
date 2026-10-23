from __future__ import annotations

import platform

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
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
from app.platform.macos.return_key_interceptor import MacOSReturnKeyInterceptor
from app.providers.asr.faster_whisper import FasterWhisperProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider
from app.providers.targets.gui_input import GuiInputTargetAdapter
from app.services.audio_recorder import AudioRecorder
from app.services.hotkey import PynputToggleHotkey
from app.services.workflow_controller import WorkflowController
from app.ui.floating_recorder import FloatingRecorder
from app.ui.paste_bubble_dialog import PasteBubbleDialog
from app.ui.shortcut_settings_dialog import ShortcutSettingsDialog
from app.ui.system_tray import SystemTray


class _Signals(QObject):
    review_ready = Signal(str, str)
    failed = Signal(str)
    hotkey_pressed = Signal()
    return_pressed = Signal()


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
        self.signals.return_pressed.connect(self._on_return)
        self.floating = FloatingRecorder()
        self.setWindowTitle("VoiceBridge")
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 14, 24, 14)
        brand = QLabel("◉  VoiceBridge")
        brand.setObjectName("brand")
        self.connection_state = QLabel("● 本地优先 · 已就绪")
        self.connection_state.setObjectName("statusChip")
        top_layout.addWidget(brand)
        top_layout.addStretch()
        top_layout.addWidget(self.connection_state)
        layout.addWidget(top_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(12)
        eyebrow = QLabel("VOICE → EDIT → PASTE")
        eyebrow.setObjectName("eyebrow")
        headline = QLabel("把语音粘贴到你的光标位置")
        headline.setObjectName("headline")
        subtitle = QLabel("先把光标放在任意输入框：快捷键开始说话，Enter 结束识别；结果可编辑，再按 Enter 粘贴。不会自动提交。")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        content_layout.addWidget(eyebrow)
        content_layout.addWidget(headline)
        content_layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(12)
        card_title = QLabel("快速录音")
        card_title.setObjectName("sectionTitle")
        card_note = QLabel("VoiceBridge 会记住开始录音前的活动窗口。录音中按 Enter 会被拦截，只用于结束录音，不会发送目标对话。")
        card_note.setObjectName("muted")
        card_note.setWordWrap(True)
        self.status = QLabel("等待录音。")
        self.status.setObjectName("targetStatus")
        self.status.setWordWrap(True)
        self.record_button = QPushButton("开始录音")
        self.record_button.setObjectName("record")
        self.record_button.clicked.connect(self._toggle_recording)
        self.shortcut_button = QPushButton("快捷键设置…")
        self.shortcut_button.clicked.connect(self._configure_shortcut)
        actions = QHBoxLayout()
        actions.addWidget(self.record_button)
        actions.addWidget(self.shortcut_button)
        actions.addStretch()
        card_layout.addWidget(card_title)
        card_layout.addWidget(card_note)
        card_layout.addWidget(self.status)
        card_layout.addLayout(actions)
        content_layout.addWidget(card)
        content_layout.addStretch()
        layout.addWidget(content)
        self.setCentralWidget(body)
        self._quitting = False
        self.tray = SystemTray(self, self._show_from_tray, self._start_from_tray, self._quit_application)
        self.hotkey_backend = None
        self.return_interceptor = None
        if self.settings.hotkey_enabled:
            self._start_hotkey()

    def _show_from_tray(self) -> None:
        self.showNormal(); self.raise_(); self.activateWindow()

    def _quit_application(self) -> None:
        self._quitting = True
        self.close()

    def _start_from_tray(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            self._toggle_recording()

    def _on_hotkey(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            self._toggle_recording()

    def _on_return(self) -> None:
        if self.controller.workflow.state is WorkflowState.RECORDING:
            self._toggle_recording()

    def _start_hotkey(self) -> None:
        try:
            if platform.system() == "Darwin":
                self.return_interceptor = MacOSReturnKeyInterceptor(
                    self.settings.hotkey,
                    lambda: self.signals.hotkey_pressed.emit(),
                    lambda: self.controller.workflow.state is WorkflowState.RECORDING,
                    lambda: self.signals.return_pressed.emit(),
                )
                self.return_interceptor.start()
            else:
                self.hotkey_backend = PynputToggleHotkey(
                    self.settings.hotkey, lambda: self.signals.hotkey_pressed.emit()
                )
                self.hotkey_backend.start()
            self.status.setText(f"全局快捷键已启用：{self.settings.hotkey}。录音中按 Enter 结束。")
        except RuntimeError as exc:
            if self.hotkey_backend:
                self.hotkey_backend.stop()
            if self.return_interceptor:
                self.return_interceptor.stop()
            self.hotkey_backend = None
            self.return_interceptor = None
            self.status.setText(f"全局快捷键不可用：{exc}")

    def _configure_shortcut(self) -> None:
        dialog = ShortcutSettingsDialog(self.settings.hotkey, self.settings.hotkey_enabled, self)
        if not dialog.exec():
            return
        if self.hotkey_backend:
            self.hotkey_backend.stop()
            self.hotkey_backend = None
        if self.return_interceptor:
            self.return_interceptor.stop()
            self.return_interceptor = None
        self.settings.hotkey = dialog.hotkey
        self.settings.hotkey_enabled = dialog.enabled.isChecked()
        self.store.save(self.settings)
        if self.settings.hotkey_enabled:
            self._start_hotkey()
        else:
            self.status.setText("全局快捷键已关闭")

    def _toggle_recording(self) -> None:
        if self.controller.workflow.state is WorkflowState.IDLE:
            try:
                self.target_snapshot = self.window_manager.capture_active_target()
                self.controller.workflow.start(); self.recorder.start()
                self.record_button.setText("停止并识别")
                self.status.setText("正在录音…按 Enter 结束并开始识别。")
                self.floating.show_recording(self.target_snapshot)
            except Exception as exc:
                self._error(str(exc))
        elif self.controller.workflow.state is WorkflowState.RECORDING:
            try:
                audio = self.recorder.stop(); self.record_button.setEnabled(False)
                preparing = "正在识别并由 DeepSeek 整理…" if self.settings.use_enhancement else "正在识别语音…"
                self.status.setText(preparing)
                self.floating.show_status(preparing, self.target_snapshot)
                self.controller.process(audio, self.settings.terminology,
                                        lambda raw, revised: self.signals.review_ready.emit(raw, revised),
                                        lambda message: self.signals.failed.emit(message), self.settings.use_enhancement)
            except Exception as exc:
                self._error(str(exc))

    def _review(self, original: str, revised: str) -> None:
        self.floating.hide(); self.status.setText("已识别。可修改文字后按 Enter 粘贴到原光标处。")
        target = self._active_cursor_target()
        dialog = PasteBubbleDialog(revised, self.target_snapshot, self)
        if dialog.exec() and dialog.text:
            try:
                self.controller.workflow.transition(WorkflowState.DISPATCHING)
                result = target.dispatch(dialog.text)
                self.controller.workflow.transition(WorkflowState.COMPLETED)
                self.status.setText(result.message)
                self.floating.show_confirmation(self.target_snapshot)
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

    def _active_cursor_target(self) -> GuiInputTargetAdapter:
        return GuiInputTargetAdapter(
            "active-cursor",
            "录音前的光标位置",
            None,
            self.target_snapshot,
            self.window_manager,
            self._copy_to_clipboard,
            self._clipboard_text,
            self._schedule,
            self.settings.gui_paste_enabled,
        )

    def _error(self, message: str) -> None:
        self.floating.hide(); self.status.setText(f"错误：{message}")
        QMessageBox.warning(self, "VoiceBridge", message)
        if self.controller.workflow.state not in {WorkflowState.IDLE, WorkflowState.FAILED}:
            self.controller.cancel()
        self._finish()

    def _finish(self) -> None:
        self.record_button.setEnabled(True); self.record_button.setText("开始录音")
        if self.controller.workflow.state in {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED}:
            self.controller.workflow.reset()

    def closeEvent(self, event) -> None:
        if not self._quitting:
            self.hide()
            event.ignore()
            return
        self.recorder.cancel()
        if self.hotkey_backend:
            self.hotkey_backend.stop()
        if self.return_interceptor:
            self.return_interceptor.stop()
        self.controller.shutdown()
        super().closeEvent(event)
