import sys

import pytest

from app.platform.macos.return_key_interceptor import MacOSReturnKeyInterceptor


@pytest.mark.skipif(sys.platform != "darwin", reason="Uses macOS Quartz key constants")
def test_macos_parser_uses_physical_keycode_for_shifted_digit() -> None:
    keycode, modifier_mask = MacOSReturnKeyInterceptor._parse_hotkey("<ctrl>+<shift>+9")

    assert keycode == 25
    assert modifier_mask

