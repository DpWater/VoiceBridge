import pytest

from app.services.hotkey import to_pynput_hotkey, to_qt_portable_text


def test_converts_macos_qt_shortcut_to_pynput() -> None:
    assert to_pynput_hotkey("Meta+Ctrl+Shift+9") == "<cmd>+<ctrl>+<shift>+9"
    assert to_qt_portable_text("<cmd>+<ctrl>+<shift>+9") == "Meta+Ctrl+Shift+9"


def test_rejects_unmodified_key() -> None:
    with pytest.raises(ValueError, match="modifier"):
        to_pynput_hotkey("9")
