
import json

import pytest

from src.agent.models import StepStatus
from src.agent.planner import (
    InvalidPlanError,
    PlanGenerationError,
    Planner,
)
from src.llm.models import LLMResponse


class FakeLLMProvider:

    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, messages, tools=None):
        self.calls.append({
            "messages": messages,
            "tools": tools
        })

        return self.response


def create_planner(content):
    response = LLMResponse(
        content=content,
        tool_calls=[]
    )

    provider = FakeLLMProvider(response)

    return Planner(provider), provider


def test_planner_creates_valid_plan():
    response_data = {
        "goal": "Implement a calculator",
        "steps": [
            {
                "id": 1,
                "description": "Inspect repository",
                "depends_on": []
            },
            {
                "id": 2,
                "description": "Implement calculator",
                "depends_on": [1]
            },
            {
                "id": 3,
                "description": "Write tests",
                "depends_on": [2]
            }
        ]
    }

    planner, provider = create_planner(
        json.dumps(response_data)
    )

    plan = planner.create_plan("Implement a calculator")

    assert plan.goal == "Implement a calculator"
    assert len(plan.steps) == 3
    assert plan.steps[0].status == StepStatus.PENDING
    assert plan.steps[1].depends_on == [1]
    assert plan.steps[2].depends_on == [2]
    assert len(provider.calls) == 1


def test_planner_sends_system_and_user_messages():
    planner, provider = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "Inspect repository",
                    "depends_on": []
                }
            ]
        })
    )

    planner.create_plan("Implement a calculator")

    messages = provider.calls[0]["messages"]

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Implement a calculator"
    assert provider.calls[0]["tools"] is None


def test_planner_rejects_empty_user_request():
    planner, _ = create_planner("{}")

    with pytest.raises(ValueError):
        planner.create_plan(" ")


def test_planner_rejects_invalid_json():
    planner, _ = create_planner(
        "This is not valid JSON"
    )

    with pytest.raises(PlanGenerationError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_empty_response():
    planner, _ = create_planner(" ")

    with pytest.raises(PlanGenerationError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_missing_schema_field():
    planner, _ = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "Inspect repository"
                }
            ]
        })
    )

    with pytest.raises(InvalidPlanError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_additional_properties():
    planner, _ = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "Inspect repository",
                    "depends_on": [],
                    "execute_python": True
                }
            ]
        })
    )

    with pytest.raises(InvalidPlanError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_duplicate_step_ids():
    planner, _ = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "First step",
                    "depends_on": []
                },
                {
                    "id": 1,
                    "description": "Second step",
                    "depends_on": []
                }
            ]
        })
    )

    with pytest.raises(InvalidPlanError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_unknown_dependencies():
    planner, _ = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "Implement calculator",
                    "depends_on": [99]
                }
            ]
        })
    )

    with pytest.raises(InvalidPlanError):
        planner.create_plan("Implement a calculator")


def test_planner_rejects_circular_dependencies():
    planner, _ = create_planner(
        json.dumps({
            "goal": "Implement a calculator",
            "steps": [
                {
                    "id": 1,
                    "description": "First step",
                    "depends_on": [2]
                },
                {
                    "id": 2,
                    "description": "Second step",
                    "depends_on": [1]
                }
            ]
        })
    )

    with pytest.raises(InvalidPlanError):
        planner.create_plan("Implement a calculator")
