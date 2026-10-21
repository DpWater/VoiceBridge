from __future__ import annotations

import tempfile
import time
import wave
from pathlib import Path

from app.models.contracts import AudioBuffer, TranscriptionResult, TranscriptSegment
from app.providers.base import SpeechRecognitionProvider


class FasterWhisperProvider(SpeechRecognitionProvider):
    provider_id = "faster-whisper"

    def __init__(self, model_name: str = "small", device: str = "auto", compute_type: str = "int8", language: str | None = None) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None

    def is_available(self) -> tuple[bool, str | None]:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False, "faster-whisper is not installed"
        return True, None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio: AudioBuffer) -> TranscriptionResult:
        available, reason = self.is_available()
        if not available:
            raise RuntimeError(reason)
        start = time.perf_counter()
        path = self._write_wav(audio)
        try:
            segments, info = self._get_model().transcribe(str(path), language=self.language, vad_filter=True)
            results = tuple(TranscriptSegment(item.text.strip(), item.start, item.end) for item in segments)
            return TranscriptionResult(
                text="".join(segment.text for segment in results).strip(),
                language=getattr(info, "language", None), model_id=self.model_name,
                elapsed_seconds=time.perf_counter() - start, segments=results,
            )
        finally:
            path.unlink(missing_ok=True)

    @staticmethod
    def _write_wav(audio: AudioBuffer) -> Path:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output:
            path = Path(output.name)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(audio.channels)
            wav.setsampwidth(audio.sample_width)
            wav.setframerate(audio.sample_rate)
            wav.writeframes(audio.samples)
        return path

    def close(self) -> None:
        self._model = None
