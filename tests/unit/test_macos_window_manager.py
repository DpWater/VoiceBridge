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


def test_activate_prefers_the_captured_process_id(monkeypatch) -> None:
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if command[0] == "/usr/bin/osascript" and "return (name" in command[-1]:
            return CompletedProcess(command, 0, "TRAE CN|4321\n", "")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(MacOSWindowManager, "is_supported", staticmethod(lambda: True))
    manager = MacOSWindowManager(runner=runner, cursor_position=lambda: (0, 0))

    assert manager.activate(TargetSnapshot("TRAE CN", process_id=4321))
    assert calls[0][0] == "/usr/bin/osascript"
    assert "unix id is 4321" in calls[0][-1]
    assert not any(command[0] == "/usr/bin/open" for command in calls)
