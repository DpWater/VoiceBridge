from app.config.store import SettingsStore
from app.models.contracts import AppSettings


def test_settings_round_trip(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    expected = AppSettings(asr_model="base", terminology=["MCP"])
    store.save(expected)
    assert store.load() == expected


def test_unknown_keys_are_ignored(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"asr_model": "tiny", "api_key": "must-not-load"}', encoding="utf-8")
    settings = SettingsStore(path).load()
    assert settings.asr_model == "tiny"
    assert not hasattr(settings, "api_key")


def test_default_hotkey_is_a_macos_command_chord() -> None:
    assert AppSettings().hotkey == "<cmd>+<ctrl>+<shift>+v"
