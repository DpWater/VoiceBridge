import pytest

from app.models.contracts import TargetSnapshot
from app.providers.targets.gui_input import GuiInputTargetAdapter


class FakeWindowManager:
    def __init__(self, activates: bool = True, pastes: bool = True) -> None:
        self.activates = activates
        self.pastes = pastes
        self.target = None

    def activate(self, target):
        self.target = target
        return self.activates

    def paste(self):
        return self.pastes


def make_target(snapshot=None, enabled=True, manager=None):
    copied = []
    snapshot = snapshot or TargetSnapshot("Cursor")
    scheduled = []
    clipboard = ["before"]
    target = GuiInputTargetAdapter(
        "cursor-current",
        "Cursor",
        "Cursor",
        snapshot,
        manager or FakeWindowManager(),
        lambda text: (copied.append(text), clipboard.__setitem__(0, text)),
        lambda: clipboard[0],
        lambda delay, callback: scheduled.append(callback),
        enabled,
    )
    return target, copied, scheduled


def test_gui_target_requires_explicit_enablement() -> None:
    target, copied, _ = make_target(enabled=False)
    with pytest.raises(RuntimeError, match="disabled"):
        target.dispatch("hello")
    assert copied == []


def test_gui_target_rejects_a_different_captured_app() -> None:
    target, copied, _ = make_target(snapshot=TargetSnapshot("Trae"))
    with pytest.raises(RuntimeError, match="not Cursor"):
        target.dispatch("hello")
    assert copied == []


def test_gui_target_activates_then_pastes_without_submit() -> None:
    manager = FakeWindowManager()
    target, copied, scheduled = make_target(manager=manager)
    result = target.dispatch("hello")
    assert manager.target == TargetSnapshot("Cursor")
    assert copied == ["hello"]
    scheduled[0]()
    assert copied == ["hello", "before"]
    assert result.status == "input"
