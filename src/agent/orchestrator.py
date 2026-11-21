from src.agent.models import (
    OrchestrationResult,
    OrchestrationStatus,
    StepStatus
)

from src.agent.planner import Planner
from src.agent.agent import Agent
from src.agent.execution_context import ExecutionContext
from src.agent.execution_manager import ExecutionManager

class Orchestrator:
    def __init__(
        self,
        planner: Planner,
        agent: Agent,
        max_agent_calls: int = 20
    ):
        if not isinstance(max_agent_calls, int) or isinstance(max_agent_calls, bool):
            raise TypeError(
                "max_agent_calls must be an integer. "
            )

        if max_agent_calls < 1:
            raise ValueError(
                "max_agent_calls must be atleast 1. "
            )

        self.planner = planner
        self.agent = agent
        self.max_agent_calls = max_agent_calls

    def run(self, user_request: str) -> OrchestrationResult:
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError(
                "User request must be a non-empty string. "
            )

        #1. Generate a structured task plan
        plan = self.planner.create_plan(user_request)

        #2. Create a fresh execution state      
        execution_manager = ExecutionManager(plan)

        context = ExecutionContext(
            user_request=user_request,
            plan=plan
        )

        agent_calls = 0

        #3. Execute eligible steps till the plan reaches a terminal state or
        #the agent-call budget is exhausted
        while True:

            #Determine the steps whose dependencies are complete
            ready_steps = execution_manager.get_ready_steps()

            #No ready steps: Determine whether execution is complete
            #or whether the plan is unexpectedly stalled
            if not ready_steps:
                pending_steps = [
                    step for step in plan.steps
                    if step.status == StepStatus.PENDING
                ]

                if pending_steps:
                    status = OrchestrationStatus.STALLED
                    message = (
                        "Execution stalled: Pending steps remain, "
                        "but no steps are currently eligible. "
                    )
                
                else:
                    status, message = self._determine_final_status(plan)

                break

            #Enforce the overall agent-call budget
            if agent_calls >= self.max_agent_calls:
                status = OrchestrationStatus.BUDGET_EXHAUSTED
                message = (
                    f"Execution stopped after reaching the maximum of "
                    f"{self.max_agent_calls} agent calls. "
                )
                break

            #Execute one ready step at a time 
            step = ready_steps[0]

            execution_manager.start_step(step.id)
            context.current_step_id = step.id

            #Construct a prompt containing the context accumulated 
            #during the previous steps
            step_prompt = self._build_step_prompt(
                context=context,
                step=step
            )

            agent_calls += 1

            try:
                agent_result = self.agent.run(step_prompt)

            except Exception as e:
                #Only the agent invocation is caught here.
                #Internal orchestration errors should not silently 
                #be converted into ordinary task failures.
                error_message = (
                    f"Agent execution failed: "
                    f"{type(e).__name__}: {e}"
                )

                execution_manager.fail_step(step.id)

                context.record_execution(
                    step_id=step.id,
                    status=StepStatus.FAILED.value,
                    result=error_message
                )

                context.current_step_id = None
                continue

            #A usable response is required to complete this step
            if not isinstance(agent_result, str) or not agent_result.strip():
                error_message = (
                    "Agent returned an empty or invalid response."
                )

                execution_manager.fail_step(step.id)

                context.record_execution(
                    step_id=step.id,
                    status=StepStatus.FAILED.value,
                    result=error_message
                )

                context.current_step_id = None
                continue

            execution_manager.complete_step(step.id)

            context.record_execution(
                step_id=step.id,
                status=StepStatus.COMPLETED.value,
                result=agent_result
            )

            #Preserve the result for subsequent steps
            context.add_observation(
                f"Agent-reported result for step {step.id} "
                f"({step.description}): {agent_result}"
            )

            context.current_step_id = None

        return OrchestrationResult(
            goal=plan.goal,
            status=status,
            plan=plan,
            execution_history=list(context.execution_history),
            message=message
        )

    @staticmethod
    def _build_step_prompt(
        context: ExecutionContext,
        step
    ) -> str:
        observations = "\n".join(
            f"- {observation}"
            for observation in context.observations
        )

        if not observations:
            observations = "No previous observations."

        history = "\n".join(
            (
                f"- Step {entry['step_id']}: "
                f"{entry['status']} — {entry['result']}"
            )
            for entry in context.execution_history
        )

        if not history:
            history = "No previous execution history."

        return f"""
        You are executing one step of a larger software engineering task.

        Original user request:
        {context.user_request}

        Overall plan goal:
        {context.plan.goal}

        Current step:
        Step {step.id}: {step.description}

        Previous observations:
        {observations}

        Previous execution history:
        {history}

        Instructions:
        1. Focus on the current step.
        2. Use repository tools when repository information is needed.
        3. Base your conclusions on actual tool results.
        4. Do not claim that an action succeeded unless you have evidence.
        5. Clearly report what you inspected, changed, or discovered.
        6. Report any errors or limitations honestly.
        7. Do not attempt to execute unrelated plan steps.

        Return a clear report of your work on the current step.
        """

    @staticmethod
    def _determine_final_status(plan):
        completed = [
            step for step in plan.steps
            if step.status == StepStatus.COMPLETED
        ]

        failed_or_blocked = [
            step for step in plan.steps
            if step.status in (
                StepStatus.FAILED,
                StepStatus.BLOCKED
            )
        ]

        if not failed_or_blocked:
            return (
                OrchestrationStatus.COMPLETED,
                "All plan steps completed."
            )

        if completed:
            return (
                OrchestrationStatus.PARTIAL_FAILURE,
                "Some steps completed, but others failed or were blocked."
            )

        return (
            OrchestrationStatus.FAILED,
            "The task could not be completed."
        )
