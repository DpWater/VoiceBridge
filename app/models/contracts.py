"""Small, explicit contracts shared across the application layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class AudioBuffer:
    samples: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = 2

    @property
    def duration_seconds(self) -> float:
        bytes_per_second = self.sample_rate * self.channels * self.sample_width
        return len(self.samples) / bytes_per_second if bytes_per_second else 0.0


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    model_id: str
    elapsed_seconds: float
    segments: tuple[TranscriptSegment, ...] = ()


@dataclass(frozen=True)
class EnhancementResult:
    text: str
    provider_id: str
    elapsed_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class DispatchResult:
    status: Literal["copied", "input", "submitted", "started"]
    message: str


@dataclass(frozen=True)
class TargetSnapshot:
    application_name: str | None = None
    process_id: int | None = None
    cursor_x: int | None = None
    cursor_y: int | None = None


@dataclass(frozen=True)
class Conversation:
    """A session exposed by a target's documented interface."""

    session_id: str
    title: str
    can_resume: bool = True
    preview: tuple[str, ...] = ()


@dataclass
class AppSettings:
    asr_model: str = "small"
    asr_device: str = "auto"
    asr_compute_type: str = "int8"
    language: str | None = None
    use_enhancement: bool = False
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 30.0
    hotkey: str = "<cmd>+<ctrl>+<shift>+9"
    hotkey_enabled: bool = False
    recording_mode: Literal["push_to_talk", "toggle"] = "push_to_talk"
    max_recording_seconds: int = 120
    default_target: str = "clipboard"
    gui_paste_enabled: bool = False
    history_enabled: bool = True
    terminology: list[str] = field(default_factory=lambda: [
        "LangGraph", "LangChain", "FastAPI", "Redis", "checkpoint", "thread_id",
        "Embedding", "Reranker", "Qdrant", "MCP", "Codex", "Cursor", "Claude Code",
    ])


@dataclass(frozen=True)
class CommandTarget:
    executable: Path
    arguments: tuple[str, ...] = ()
