
import pytest

from src.agent.models import (
    PlanStep,
    TaskPlan,
    StepStatus,
    OrchestrationStatus
)
from src.agent.orchestrator import Orchestrator, OrchestrationStatus


class FakePlanner:

    def __init__(self, plan):
        self.plan = plan
        self.calls = []

    def create_plan(self, user_request):
        self.calls.append(user_request)
        return self.plan


class FakeAgent:

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def run(self, user_input):
        self.calls.append(user_input)

        if not self.responses:
            raise RuntimeError("No more fake responses available.")

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def create_plan():
    return TaskPlan(
        goal="Inspect the repository",
        steps=[
            PlanStep(1, "Inspect repository", []),
            PlanStep(2, "Identify failing tests", [1]),
            PlanStep(3, "Inspect dependencies", [])
        ]
    )


def test_orchestrator_generates_plan():
    plan = create_plan()
    planner = FakePlanner(plan)
    agent = FakeAgent(["Step completed."] * 3)

    orchestrator = Orchestrator(planner, agent)

    result = orchestrator.run("Inspect my repository.")

    assert planner.calls == ["Inspect my repository."]
    assert result.plan is plan


def test_orchestrator_completes_all_steps():
    planner = FakePlanner(create_plan())
    agent = FakeAgent([
        "Repository inspected.",
        "Failing tests identified.",
        "Dependencies inspected."
    ])

    orchestrator = Orchestrator(planner, agent)

    result = orchestrator.run("Inspect my repository.")

    assert result.status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) == 3
    assert len(result.failed_steps) == 0
    assert len(result.blocked_steps) == 0


def test_orchestrator_executes_steps_in_dependency_order():
    planner = FakePlanner(create_plan())
    agent = FakeAgent([
        "Repository inspected.",
        "Failing tests identified.",
        "Dependencies inspected."
    ])

    orchestrator = Orchestrator(planner, agent)

    orchestrator.run("Inspect my repository.")

    assert len(agent.calls) == 3

    assert "Inspect repository" in agent.calls[0]
    assert "Identify failing tests" in agent.calls[1]
    assert "Inspect dependencies" in agent.calls[2]


def test_orchestrator_rejects_empty_request():
    planner = FakePlanner(create_plan())
    agent = FakeAgent([])

    orchestrator = Orchestrator(planner, agent)

    with pytest.raises(ValueError):
        orchestrator.run("")

def test_orchestrator_continues_independent_steps_after_failure():
    planner = FakePlanner(create_plan())

    agent = FakeAgent([
        RuntimeError("Repository inspection failed."),
        "Dependencies inspected successfully."
    ])

    orchestrator = Orchestrator(planner, agent)

    result = orchestrator.run("Inspect my repository.")

    assert result.status == OrchestrationStatus.PARTIAL_FAILURE

    assert result.plan.steps[0].status == StepStatus.FAILED
    assert result.plan.steps[1].status == StepStatus.BLOCKED
    assert result.plan.steps[2].status == StepStatus.COMPLETED

    assert len(agent.calls) == 2

def test_orchestrator_rejects_empty_agent_response():
    planner = FakePlanner(create_plan())

    agent = FakeAgent([
        "",
        "Dependencies inspected successfully."
    ])

    orchestrator = Orchestrator(planner, agent)

    result = orchestrator.run("Inspect my repository.")

    assert result.status == OrchestrationStatus.PARTIAL_FAILURE

    assert result.plan.steps[0].status == StepStatus.FAILED
    assert result.plan.steps[1].status == StepStatus.BLOCKED
    assert result.plan.steps[2].status == StepStatus.COMPLETED

def test_orchestrator_stops_when_agent_call_budget_is_exhausted():
    planner = FakePlanner(create_plan())

    agent = FakeAgent([
        "Repository inspected successfully.",
        "This response should never be used."
    ])

    orchestrator = Orchestrator(
        planner=planner,
        agent=agent,
        max_agent_calls=1
    )

    result = orchestrator.run("Inspect my repository.")

    assert result.status == OrchestrationStatus.BUDGET_EXHAUSTED

    assert len(agent.calls) == 1

    assert result.plan.steps[0].status == StepStatus.COMPLETED
    assert result.plan.steps[1].status == StepStatus.PENDING
    assert result.plan.steps[2].status == StepStatus.PENDING

def test_orchestrator_reports_total_failure():
    planner = FakePlanner(create_plan())

    agent = FakeAgent([
        RuntimeError("Repository inspection failed."),
        RuntimeError("Dependency inspection failed.")
    ])

    orchestrator = Orchestrator(planner, agent)

    result = orchestrator.run("Inspect my repository.")

    assert result.status == OrchestrationStatus.FAILED

    assert result.plan.steps[0].status == StepStatus.FAILED
    assert result.plan.steps[1].status == StepStatus.BLOCKED
    assert result.plan.steps[2].status == StepStatus.FAILED

    assert len(result.completed_steps) == 0


