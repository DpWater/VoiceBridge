from app.models.contracts import AudioBuffer
from app.providers.asr.faster_whisper import FasterWhisperProvider


def test_wav_writer_creates_real_pcm_wav() -> None:
    audio = AudioBuffer(samples=b"\x00\x00" * 160, sample_rate=16_000)
    path = FasterWhisperProvider._write_wav(audio)
    try:
        assert path.read_bytes()[:4] == b"RIFF"
    finally:
        path.unlink()
