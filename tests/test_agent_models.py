import pytest
from src.agent.models import (
    PlanStep,
    TaskPlan,
    StepStatus
)

def test_plan_step_creation():
    step = PlanStep(
        id=1,
        description="Inspect repository"
    )

    assert step.id == 1
    assert step.description == "Inspect repository"
    assert step.depends_on == []
    assert step.status == StepStatus.PENDING

def test_plan_step_with_dependencies():
    step = PlanStep(
        id=2,
        description="Implement calculator",
        depends_on=[1]
    )

    assert step.depends_on == [1]

def test_plan_step_rejects_invalid_id():
    with pytest.raises(ValueError):
        PlanStep(id=0, description="Inspect repository")

def test_plan_step_rejects_boolean_id():
    with pytest.raises(TypeError):
        PlanStep(id=True, description="Inspect repository")

def test_plan_step_rejects_empty_description():
    with pytest.raises(ValueError):
        PlanStep(id=1, description="   ")

def test_plan_step_rejects_duplicate_dependencies():
    with pytest.raises(ValueError):
        PlanStep(
            id=3,
            description="Run tests",
            depends_on=[1, 1]
        )

def test_plan_step_rejects_self_dependency():
    with pytest.raises(ValueError):
        PlanStep(
            id=1,
            description="Inspect repository",
            depends_on=[1]
        )

def test_plan_step_rejects_invalid_status():
    with pytest.raises(TypeError):
        PlanStep(
            id=1,
            description="Inspect repository",
            status="finished"
        )

def test_task_plan_creation():
    plan = TaskPlan(
        goal="Implement a calculator",
        steps=[
            PlanStep(1, "Inspect repository"),
            PlanStep(2, "Implement calculator", [1]),
            PlanStep(3, "Write tests", [2]),
        ]
    )

    assert plan.goal == "Implement a calculator"
    assert len(plan.steps) == 3

def test_task_plan_rejects_empty_goal():
    with pytest.raises(ValueError):
        TaskPlan(goal=" ", steps=[
            PlanStep(1, "Inspect repository")
        ])

def test_task_plan_rejects_empty_steps():
    with pytest.raises(ValueError):
        TaskPlan(goal="Implement calculator", steps=[])

def test_task_plan_rejects_duplicate_step_ids():
    with pytest.raises(ValueError):
        TaskPlan(
            goal="Implement calculator",
            steps=[
                PlanStep(1, "Inspect repository"),
                PlanStep(1, "Implement calculator")
            ]
        )

def test_task_plan_rejects_unknown_dependency():
    with pytest.raises(ValueError):
        TaskPlan(
            goal="Implement calculator",
            steps=[
                PlanStep(1, "Inspect repository", [99])
            ]
        )

def test_task_plan_rejects_direct_cycle():
    with pytest.raises(ValueError, match="Circular dependencies"):
        TaskPlan(
            goal="Implement calculator",
            steps=[
                PlanStep(1, "First step", [2]),
                PlanStep(2, "Second step", [1])
            ]
        )

def test_task_plan_rejects_indirect_cycle():
    with pytest.raises(ValueError, match="Circular dependencies"):
        TaskPlan(
            goal="Implement calculator",
            steps=[
                PlanStep(1, "First step", [2]),
                PlanStep(2, "Second step", [3]),
                PlanStep(3, "Third step", [1])
            ]
        )