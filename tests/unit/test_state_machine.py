import pytest

from app.core.state_machine import InvalidTransition, Workflow, WorkflowState


def test_happy_path_and_reset() -> None:
    flow = Workflow()
    assert flow.start()
    for state in (WorkflowState.TRANSCRIBING, WorkflowState.REVIEWING, WorkflowState.DISPATCHING, WorkflowState.COMPLETED):
        flow.transition(state)
    flow.reset()
    assert flow.state is WorkflowState.IDLE
    assert flow.task_id is None


def test_prevents_overlapping_tasks() -> None:
    flow = Workflow(); flow.start()
    with pytest.raises(InvalidTransition):
        flow.start()


def test_cancel_from_processing() -> None:
    flow = Workflow(); flow.start(); flow.transition(WorkflowState.TRANSCRIBING)
    flow.transition(WorkflowState.CANCELLED)
    assert flow.state is WorkflowState.CANCELLED
