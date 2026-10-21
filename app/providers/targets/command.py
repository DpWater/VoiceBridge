from __future__ import annotations

import subprocess

from app.models.contracts import CommandTarget, DispatchResult
from app.providers.base import TargetAdapter


class GenericCommandAdapter(TargetAdapter):
    """Runs an explicitly configured executable; voice text is delivered through stdin."""
    target_id = "command"

    def __init__(self, target: CommandTarget) -> None:
        self.target = target

    def dispatch(self, text: str) -> DispatchResult:
        if not self.target.executable.is_file():
            raise RuntimeError(f"Configured command does not exist: {self.target.executable}")
        process = subprocess.Popen([str(self.target.executable), *self.target.arguments], stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        if process.stdin is None:
            raise RuntimeError("Could not open stdin for configured command")
        process.stdin.write(text)
        process.stdin.close()
        return DispatchResult("started", "Configured command was started with the instruction on stdin.")
