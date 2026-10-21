from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class WorkflowState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ENHANCING = "enhancing"
    REVIEWING = "reviewing"
    DISPATCHING = "dispatching"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.IDLE: {WorkflowState.RECORDING},
    WorkflowState.RECORDING: {WorkflowState.TRANSCRIBING, WorkflowState.CANCELLED, WorkflowState.FAILED},
    WorkflowState.TRANSCRIBING: {WorkflowState.ENHANCING, WorkflowState.REVIEWING, WorkflowState.CANCELLED, WorkflowState.FAILED},
    WorkflowState.ENHANCING: {WorkflowState.REVIEWING, WorkflowState.CANCELLED, WorkflowState.FAILED},
    WorkflowState.REVIEWING: {WorkflowState.DISPATCHING, WorkflowState.CANCELLED},
    WorkflowState.DISPATCHING: {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.COMPLETED: {WorkflowState.IDLE},
    WorkflowState.FAILED: {WorkflowState.IDLE, WorkflowState.REVIEWING},
    WorkflowState.CANCELLED: {WorkflowState.IDLE},
}


class InvalidTransition(RuntimeError):
    pass


@dataclass
class Workflow:
    state: WorkflowState = WorkflowState.IDLE
    task_id: str | None = None

    def start(self) -> str:
        if self.state is not WorkflowState.IDLE:
            raise InvalidTransition("A recording task is already active")
        self.task_id = uuid4().hex
        self.transition(WorkflowState.RECORDING)
        return self.task_id

    def transition(self, next_state: WorkflowState) -> None:
        if next_state not in _ALLOWED[self.state]:
            raise InvalidTransition(f"Cannot transition from {self.state} to {next_state}")
        self.state = next_state

    def reset(self) -> None:
        if self.state not in {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED}:
            raise InvalidTransition("Only a finished task can be reset")
        self.transition(WorkflowState.IDLE)
        self.task_id = None
