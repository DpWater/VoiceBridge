from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.contracts import AudioBuffer, DispatchResult, EnhancementResult, TranscriptionResult


class SpeechRecognitionProvider(ABC):
    provider_id: str

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]: ...

    @abstractmethod
    def transcribe(self, audio: AudioBuffer) -> TranscriptionResult: ...

    def close(self) -> None:
        """Release an optional model cache."""


class TextEnhancementProvider(ABC):
    provider_id: str

    @abstractmethod
    def enhance(self, text: str, terminology: list[str]) -> EnhancementResult: ...


class TargetAdapter(ABC):
    target_id: str

    @abstractmethod
    def dispatch(self, text: str) -> DispatchResult: ...
