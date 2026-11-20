from src.agent.models import TaskPlan, PlanStep, StepStatus

class ExecutionManager:
    def __init__(self, plan: TaskPlan):
        if not isinstance(plan, TaskPlan):
            raise TypeError(
                "plan must be an instance of TaskPlan. "
            )

        self.plan = plan

    def get_step(self, step_id: int):
        for step in self.plan.steps:
            if step.id == step_id:
                return step

        raise ValueError(
            f"Unknown step ID: {step_id}"
        )

    def get_ready_steps(self):
        ready_steps = []

        for step in self.plan.steps:
            if step.status != StepStatus.PENDING:
                continue

            dependencies_completed = all(
                self.get_step(dependency_id).status == StepStatus.COMPLETED
                for dependency_id in step.depends_on
            )

            if dependencies_completed:
                ready_steps.append(step)

        return ready_steps

    def start_step(self, step_id: int):
        step = self.get_step(step_id)

        if step.status != StepStatus.PENDING:
            raise ValueError(
                f"Cannot start step {step_id}: "
                f"Currrent status is {step.status.value}."
            )

        ready_step_ids = {
            ready_step.id 
            for ready_step in self.get_ready_steps()
        }

        if step_id not in ready_step_ids:
            raise ValueError(
                f"Cannot start step {step_id}: "
                "one or more dependencies are incomplete. "
            )

        step.status = StepStatus.IN_PROGRESS

    def complete_step(self, step_id: int):
        step = self.get_step(step_id)

        if step.status != StepStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot complete step {step_id}: "
                "step is not in progress. "
            )

        step.status = StepStatus.COMPLETED

    def fail_step(self, step_id: int):
        step = self.get_step(step_id)

        if step.status != StepStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot fail step {step_id}: "
                "step is not in progress. "
            )

        step.status = StepStatus.FAILED
        self._block_dependent_steps(step_id)

    def _block_dependent_steps(self, failed_step_id: int):
        for step in self.plan.steps:
            if (
                step.status == StepStatus.PENDING
                and failed_step_id in step.depends_on
            ):
                step.status = StepStatus.BLOCKED
                self._block_dependent_steps(step.id)

    def is_complete(self):
        return all(
            step.status == StepStatus.COMPLETED
            for step in self.plan.steps
        )