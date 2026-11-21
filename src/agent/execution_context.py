from dataclasses import dataclass, field
from src.agent.models import TaskPlan

@dataclass
class ExecutionContext:
    user_request: str
    plan: TaskPlan
    current_step_id: int | None = None
    observations: list[str] = field(default_factory=list)
    execution_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.user_request, str) or not self.user_request.strip():
            raise ValueError(
                "User request must be a non-empty string. "
            )

        if not isinstance(self.plan, TaskPlan):
            raise TypeError(
                "plan must be a TaskPlan instance. "
            )

        if self.current_step_id is not None:
            if not isinstance(self.current_step_id, int) or isinstance(self.current_step_id, bool):
                raise TypeError(
                    "current_step_id must be an integer or None. "
                )

            if self.current_step_id < 1:
                raise ValueError(
                    "current_step_id must be positive. "
                )

            if not any(
                step.id == self.current_step_id
                for step in self.plan.steps
            ):
                raise ValueError(
                    "current_step_id does not exist in the plan. "
                )

            if not isinstance(self.observations, list):
                raise TypeError(
                    "observations must be a list. "
                )

            if not all(isinstance(item, str) for item in self.observations):
                raise TypeError(
                    "Every observation must be a string. "
                )

            if not isinstance(self.execution_history, list):
                raise TypeError(
                    "execution_history must be a list. "
                )

    def add_observation(self, observation: str):
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(
                "observation must be a non-empty string. "
            )

        self.observations.append(observation)

    def record_execution(
            self,
            step_id: int,
            status: int,
            result: str | None
    ):
        if not isinstance(step_id, int) or isinstance(step_id, bool):
            raise TypeError(
                "step_id must be an integer. "
            )

        if not any(step.id == step_id for step in self.plan.steps):
            raise ValueError(
                f"Unknown step ID: {step_id}"
            )

        if not isinstance(status, str) or not status.strip():
            raise ValueError(
                "status must be a non-empty string. "
            )

        if result is not None and not isinstance(result, str):
            raise TypeError(
                "result must be a string or None. "
            )

        self.execution_history.append({
            "step_id": step_id,
            "status": status,
            "result": result
        })