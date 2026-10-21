from app.core.state_machine import WorkflowState
from app.models.contracts import AudioBuffer, EnhancementResult, TranscriptionResult
from app.providers.base import SpeechRecognitionProvider, TextEnhancementProvider
from app.services.workflow_controller import WorkflowController


class FakeASR(SpeechRecognitionProvider):
    provider_id = "fake"
    def is_available(self): return True, None
    def transcribe(self, audio): return TranscriptionResult("lang graph checkpoint", "zh", "fake", 0.01)


class FakeLLM(TextEnhancementProvider):
    provider_id = "fake"
    def enhance(self, text, terminology): return EnhancementResult("LangGraph checkpoint", "fake", 0.01)


def test_process_runs_asr_then_llm() -> None:
    controller = WorkflowController(FakeASR(), FakeLLM())
    controller.workflow.start()
    received, errors = [], []
    controller.process(AudioBuffer(b"\0\0", 16000), ["LangGraph"],
                       lambda raw, revised: received.append((raw, revised)), errors.append, True)
    controller._executor.shutdown(wait=True)
    assert received == [("lang graph checkpoint", "LangGraph checkpoint")]
    assert errors == []
    assert controller.workflow.state is WorkflowState.REVIEWING
