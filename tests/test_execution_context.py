import pytest

from src.agent.models import PlanStep, TaskPlan
from src.agent.execution_context import ExecutionContext

def create_plan():
    return TaskPlan(
        goal="Implement a calculator",
        steps=[
            PlanStep(1,"Inspect repository",[]),
            PlanStep(2,"Implement calculator",[1])
        ]
    )

def test_execution_context_creation():
    context = ExecutionContext(
        user_request="Implement a calculator",
        plan=create_plan()
    )

    assert context.user_request == "Implement a calculator"
    assert context.current_step_id is None
    assert context.observations == []
    assert context.execution_history == []

def test_execution_context_requires_valid_request():

    with pytest.raises(ValueError):
        ExecutionContext("", create_plan())

def test_execution_context_requires_task_plan():

    with pytest.raises(TypeError):
        ExecutionContext("Implement calculator", "not a plan")

def test_execution_context_validates_current_step():

    with pytest.raises(ValueError):
        ExecutionContext(
            "Implement calculator",
            create_plan(),
            current_step_id=99
        )

def test_execution_context_validates_current_step_type():

    with pytest.raises(TypeError):
        ExecutionContext(
            "Implement calculator",
            create_plan(),
            current_step_id=True
        )

def test_observations_are_independent():

    first = ExecutionContext("Task one", create_plan())
    second = ExecutionContext("Task two", create_plan())

    first.add_observation("Found calculator.py")

    assert len(first.observations) == 1
    assert len(second.observations) == 0

def test_add_observation():

    context = ExecutionContext("Implement calculator", create_plan())

    context.add_observation("Found calculator.py")

    assert context.observations == ["Found calculator.py"]

def test_reject_empty_observation():

    context = ExecutionContext("Implement calculator", create_plan())

    with pytest.raises(ValueError):
        context.add_observation(" ")

def test_record_execution():

    context = ExecutionContext("Implement calculator", create_plan())

    context.record_execution(
        step_id=1,
        status="completed",
        result="Repository inspected."
    )

    assert len(context.execution_history) == 1
    assert context.execution_history[0]["step_id"] == 1
    assert context.execution_history[0]["status"] == "completed"

def test_record_execution_rejects_unknown_step():

    context = ExecutionContext("Implement calculator", create_plan())

    with pytest.raises(ValueError):
        context.record_execution(99, "completed", "Done")

def test_record_execution_rejects_invalid_result():
    context = ExecutionContext("Implement calculator", create_plan())

    with pytest.raises(TypeError):
        context.record_execution(1,"completed",123)

def test_record_execution_rejects_boolean_step_id():

    context = ExecutionContext("Implement calculator", create_plan())

    with pytest.raises(TypeError):
        context.record_execution(True, "completed", "Done")