
import pytest

from src.agent.models import PlanStep, TaskPlan, StepStatus
from src.agent.execution_manager import ExecutionManager


def create_plan():
    return TaskPlan(
        goal="Implement a calculator",
        steps=[
            PlanStep(
                id=1,
                description="Inspect repository",
                depends_on=[]
            ),
            PlanStep(
                id=2,
                description="Implement calculator",
                depends_on=[1]
            ),
            PlanStep(
                id=3,
                description="Write tests",
                depends_on=[2]
            ),
            PlanStep(
                id=4,
                description="Update documentation",
                depends_on=[2]
            )
        ]
    )


def test_execution_manager_requires_task_plan():
    with pytest.raises(TypeError):
        ExecutionManager("not a plan")


def test_get_ready_steps_returns_only_independent_steps():
    manager = ExecutionManager(create_plan())

    ready_steps = manager.get_ready_steps()

    assert [step.id for step in ready_steps] == [1]


def test_start_step_changes_status():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)

    assert manager.get_step(1).status == StepStatus.IN_PROGRESS


def test_cannot_start_step_with_incomplete_dependency():
    manager = ExecutionManager(create_plan())

    with pytest.raises(ValueError):
        manager.start_step(2)


def test_cannot_start_non_pending_step():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)

    with pytest.raises(ValueError):
        manager.start_step(1)


def test_complete_step_changes_status():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)
    manager.complete_step(1)

    assert manager.get_step(1).status == StepStatus.COMPLETED


def test_cannot_complete_step_that_is_not_in_progress():
    manager = ExecutionManager(create_plan())

    with pytest.raises(ValueError):
        manager.complete_step(1)


def test_next_step_becomes_ready_after_dependency_completes():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)
    manager.complete_step(1)

    ready_steps = manager.get_ready_steps()

    assert [step.id for step in ready_steps] == [2]


def test_independent_steps_can_be_ready_simultaneously():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)
    manager.complete_step(1)

    manager.start_step(2)
    manager.complete_step(2)

    ready_steps = manager.get_ready_steps()

    assert [step.id for step in ready_steps] == [3, 4]


def test_fail_step_changes_status():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)
    manager.fail_step(1)

    assert manager.get_step(1).status == StepStatus.FAILED


def test_failure_blocks_dependent_steps():
    manager = ExecutionManager(create_plan())

    manager.start_step(1)
    manager.complete_step(1)

    manager.start_step(2)
    manager.fail_step(2)

    assert manager.get_step(3).status == StepStatus.BLOCKED
    assert manager.get_step(4).status == StepStatus.BLOCKED


def test_blocking_propagates_to_downstream_steps():
    plan = TaskPlan(
        goal="Example",
        steps=[
            PlanStep(1, "First", []),
            PlanStep(2, "Second", [1]),
            PlanStep(3, "Third", [2]),
            PlanStep(4, "Fourth", [3])
        ]
    )

    manager = ExecutionManager(plan)

    manager.start_step(1)
    manager.fail_step(1)

    assert manager.get_step(2).status == StepStatus.BLOCKED
    assert manager.get_step(3).status == StepStatus.BLOCKED
    assert manager.get_step(4).status == StepStatus.BLOCKED


def test_plan_is_complete_only_when_all_steps_are_completed():
    manager = ExecutionManager(create_plan())

    assert manager.is_complete() is False

    manager.start_step(1)
    manager.complete_step(1)

    assert manager.is_complete() is False


def test_unknown_step_raises_error():
    manager = ExecutionManager(create_plan())

    with pytest.raises(ValueError):
        manager.get_step(99)


def test_cannot_fail_step_that_is_not_in_progress():
    manager = ExecutionManager(create_plan())

    with pytest.raises(ValueError):
        manager.fail_step(1)
