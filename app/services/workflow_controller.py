from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from app.core.state_machine import Workflow, WorkflowState
from app.models.contracts import AudioBuffer, EnhancementResult, TranscriptionResult
from app.providers.base import SpeechRecognitionProvider, TextEnhancementProvider


class WorkflowController:
    """Keeps blocking model work off the Qt event loop and rejects stale results."""
    def __init__(self, asr: SpeechRecognitionProvider, llm: TextEnhancementProvider | None = None) -> None:
        self.workflow, self.asr, self.llm = Workflow(), asr, llm
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="voicebridge")

    def process(self, audio: AudioBuffer, terminology: list[str], on_review: Callable[[str, str], None],
                on_error: Callable[[str], None], enhance: bool = False) -> str:
        task_id = self.workflow.task_id
        if not task_id or self.workflow.state is not WorkflowState.RECORDING:
            raise RuntimeError("There is no active recording task")
        self.workflow.transition(WorkflowState.TRANSCRIBING)
        self._executor.submit(self._run, task_id, audio, terminology, on_review, on_error, enhance)
        return task_id

    def _run(self, task_id: str, audio: AudioBuffer, terminology: list[str], on_review, on_error, enhance: bool) -> None:
        try:
            transcript: TranscriptionResult = self.asr.transcribe(audio)
            if task_id != self.workflow.task_id or self.workflow.state is WorkflowState.CANCELLED:
                return
            revised = transcript.text
            if enhance and self.llm:
                self.workflow.transition(WorkflowState.ENHANCING)
                try:
                    response: EnhancementResult = self.llm.enhance(transcript.text, terminology)
                    revised = response.text
                except Exception:
                    revised = transcript.text  # Review remains safe and fully editable.
            if task_id != self.workflow.task_id or self.workflow.state is WorkflowState.CANCELLED:
                return
            self.workflow.transition(WorkflowState.REVIEWING)
            on_review(transcript.text, revised)
        except Exception as exc:
            if task_id == self.workflow.task_id and self.workflow.state is not WorkflowState.CANCELLED:
                self.workflow.transition(WorkflowState.FAILED)
                on_error(str(exc))

    def cancel(self) -> None:
        if self.workflow.state in {WorkflowState.RECORDING, WorkflowState.TRANSCRIBING, WorkflowState.ENHANCING, WorkflowState.REVIEWING, WorkflowState.DISPATCHING}:
            self.workflow.transition(WorkflowState.CANCELLED)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
