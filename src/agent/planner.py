import json

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from src.agent.models import PlanStep, TaskPlan
from src.llm.base import LLMProvider

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "maxItems": 20,
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 500
                    },
                    "depends_on": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "uniqueItems": True
                    }
                },
                "required": [
                    "id",
                    "description",
                    "depends_on"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": ["goal", "steps"],
    "addtionalProperties": False
}

SYSTEM_PROMPT = """
You are the planning component of Vastukaar, an autonomous
software engineering agent.

Your responsibility is to convert a user's software engineering
request into a clear, ordered, actionable execution plan.

Planning rules:

1. Understand the user's overall engineering objective.
2. Break the objective into small, concrete, actionable steps.
3. Order the steps logically.
4. Use dependencies to indicate which steps must be completed
   before other steps can begin.
5. Every dependency must refer to an existing step ID.
6. Do not create circular dependencies.
7. Do not include steps that are unrelated to the user's objective.
8. Include repository inspection when the task requires
   understanding existing code.
9. Include testing and verification when the task involves
   implementing or modifying software.
10. Do not claim that any step has already been executed.
11. Do not include code or tool calls in the plan.
12. Keep the plan concise and practical.

Return only valid JSON. Do not use Markdown code fences.

The JSON must follow this structure:

{
    "goal": "A concise description of the objective",
    "steps": [
        {
            "id": 1,
            "description": "Description of the first step",
            "depends_on": []
        }
    ]
}

Use sequential positive integer IDs beginning with 1.
Every step must include all three fields.
Do not include additional fields.
"""

class PlanGenerationError(Exception):
    #Raised when the LLM cannot produce a usable plan.
    pass

class InvalidPlanError(Exception):
    #Raised when the generated plan violates planning rules
    pass

class Planner:

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def create_plan(self, user_request: LLMProvider):
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError(
                "User request must be a non-empty string. "
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_request
            }
        ]

        response = self.llm_provider.generate(messages=messages)

        if response.tool_calls:
            raise PlanGenerationError(
                "The planning model returned tool calls instead of a plan. "
            )

        if not isinstance(response.content, str) or not response.content.strip():
            raise PlanGenerationError(
                "The planning model returned an empty response. "
            )

        try:
            plan_data = json.loads(response.content)

        except json.JSONDecodeError as e:
            raise PlanGenerationError(
                "The planning model returned invalid JSON. "
            ) from e

        try:
            validate(
                instance=plan_data,
                schema=PLAN_SCHEMA
            )

        except ValidationError as e:
            raise InvalidPlanError(
                f"Generated plan does not match required schema: {e.message}"
            ) from e

        try:
            steps = [
                PlanStep(
                    id=step["id"],
                    description=step["description"],
                    depends_on=step["depends_on"]
                )
                for step in plan_data["steps"]
            ]

            return TaskPlan(
                goal=plan_data["goal"],
                steps=steps
            )

        except (TypeError, ValueError) as e:
            raise InvalidPlanError(
                f"Generated plan violates planning rules: {e}"
            ) from e