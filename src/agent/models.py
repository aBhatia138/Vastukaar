from dataclasses import dataclass, field
from enum import Enum

class OrchestrationStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    STALLED = "stalled"

class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class PlanStep:
    id: int
    description: str
    depends_on: list[int] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING

    def __post_init__(self):
        if not isinstance(self.id, int) or isinstance(self.id, bool):
            raise TypeError(
                "Step ID must be an integer. "
            )

        if self.id < 1:
            raise ValueError(
                "Step ID must be atleast 1. "
            )

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError(
                "Step description must be a non-empty string. "
            )

        if not isinstance(self.depends_on, list):
            raise TypeError(
                "depends_on must be a list. "
            )

        if any(
            not isinstance(dependency, int) or isinstance(dependency, bool)
            for dependency in self.depends_on
        ):
            raise TypeError(
                "Dependency IDs must be integers. "
            )

        if any(dependency < 1 for dependency in self.depends_on):
            raise ValueError(
                "Dependency IDs must be atleast 1. "
            )

        if len(self.depends_on) != len(set(self.depends_on)):
            raise ValueError(
                "Duplicate dependencies are not permitted. "
            )

        if self.id in self.depends_on:
            raise ValueError(
                "A step cannot depend on itself. "
            )

        if not isinstance(self.status, StepStatus):
            raise TypeError(
                "status must be a StepStatus value. "
            )

@dataclass
class TaskPlan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError(
                "Task goal cannot be empty. "
            )

        if not isinstance(self.steps, list):
            raise TypeError(
                "steps must be a list. "
            )

        if not all(isinstance(step, PlanStep) for step in self.steps):
            raise TypeError(
                "Every step's plan must be a PlanStep instance. "
            )

        self.validate()

    def validate(self):
        step_ids = [step.id for step in self.steps]

        if not self.steps:
            raise ValueError(
                "A task plan must contain atleast one step. "
            )

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "Step IDs must be unique. "
            )

        known_ids = set(step_ids)

        for step in self.steps:
            for dependency in step.depends_on:
                if dependency not in known_ids:
                    raise ValueError(
                        f"Step {step.id} depends on unknown step {dependency}. "
                    )

        self._validate_acyclic_dependencies()

    def _validate_acyclic_dependencies(self):
        #Reject circular dependencies using DFS

        dependencies = {
            step.id: step.depends_on
            for step in self.steps
        }

        visiting = set()
        visited = set()

        def visit(step_id):
            if step_id in visiting:
                raise ValueError(
                    "Circular dependencies detected. "
                )

            if step_id in visited:
                return

            visiting.add(step_id)

            for dependency in dependencies[step_id]:
                visit(dependency)

            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in dependencies:
            visit(step_id)

@dataclass
class OrchestrationResult:
    goal: str
    status: OrchestrationStatus
    plan: TaskPlan
    execution_history: list[dict] = field(default_factory=list)
    message: str = ""

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError(
                "goal must be a non-empty string. "
            )

        if not isinstance(self.status, OrchestrationStatus):
            raise TypeError(
                "Status must be an OrchestrationStatus. "
            )

        if not isinstance(self.plan, TaskPlan):
            raise TypeError(
                "plan must be a TaskPlan. "
            )

        if not isinstance(self.execution_history, list):
            raise TypeError(
                "execution_history must be a list. "
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "message must be a string. "
            )

    @property
    def failed_steps(self) -> list[PlanStep]:
        return [
            step for step in self.plan.steps
            if step.status == StepStatus.FAILED
        ]

    @property
    def blocked_steps(self) -> list[PlanStep]:
        return [
            step for step in self.plan.steps
            if step.status == StepStatus.BLOCKED
        ]

    @property
    def completed_steps(self) -> list[PlanStep]:
        return [
            step for step in self.plan.steps
            if step.status == StepStatus.COMPLETED
        ]
    
    