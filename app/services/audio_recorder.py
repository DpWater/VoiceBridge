from __future__ import annotations

import threading
import time

from app.models.contracts import AudioBuffer


class AudioRecorder:
    """Captures real mono PCM data and keeps audio only in memory."""
    def __init__(self, sample_rate: int = 16_000, max_seconds: int = 120, device: int | str | None = None) -> None:
        self.sample_rate, self.max_seconds, self.device = sample_rate, max_seconds, device
        self._stream = None
        self._chunks: list[bytes] = []
        self._started_at: float | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice is not installed") from exc
        with self._lock:
            if self._stream is not None:
                raise RuntimeError("Recording is already active")
            self._chunks = []
            self._started_at = time.monotonic()
            self._stream = sd.RawInputStream(samplerate=self.sample_rate, channels=1, dtype="int16",
                                              device=self.device, callback=self._on_audio)
            self._stream.start()

    def _on_audio(self, indata, frames, time_info, status) -> None:
        if status:
            return  # Sounddevice exposes transient status; capture remains usable.
        if self._started_at and time.monotonic() - self._started_at < self.max_seconds:
            self._chunks.append(bytes(indata))

    def stop(self) -> AudioBuffer:
        with self._lock:
            if self._stream is None:
                raise RuntimeError("No recording is active")
            self._stream.stop(); self._stream.close(); self._stream = None
            samples = b"".join(self._chunks)
            self._chunks = []
        if not samples:
            raise RuntimeError("No audio was captured")
        return AudioBuffer(samples, self.sample_rate)

    def cancel(self) -> None:
        with self._lock:
            if self._stream is not None:
                self._stream.stop(); self._stream.close(); self._stream = None
            self._chunks = []
