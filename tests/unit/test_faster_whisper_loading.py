from app.providers.asr.faster_whisper import FasterWhisperProvider


def test_model_loading_is_local_only(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeWhisperModel:
        def __init__(self, *args, **kwargs) -> None:
            captured.update(kwargs)

    import faster_whisper

    monkeypatch.setattr(faster_whisper, "WhisperModel", FakeWhisperModel)
    provider = FasterWhisperProvider("tiny", "cpu", "int8")

    provider._get_model()

    assert captured["local_files_only"] is True
