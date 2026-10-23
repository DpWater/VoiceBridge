from subprocess import CompletedProcess

from app.models.contracts import TargetSnapshot
from app.platform.macos.window_manager import MacOSWindowManager


def test_capture_and_activate_use_argument_lists(monkeypatch) -> None:
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if command[0] == "/usr/bin/osascript":
            return CompletedProcess(command, 0, "Cursor\n", "")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(MacOSWindowManager, "is_supported", staticmethod(lambda: True))
    manager = MacOSWindowManager(runner=runner, cursor_position=lambda: (320, 640))
    assert manager.capture_active_target() == TargetSnapshot("Cursor", cursor_x=320, cursor_y=640)
    assert manager.activate(TargetSnapshot("Cursor"))
    assert manager.paste()
    assert calls[1] == ["/usr/bin/open", "-a", "Cursor"]
