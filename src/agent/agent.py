
import json

from src.llm.base import LLMProvider
from src.tools.definitions import TOOLS
from src.tools.registry import ToolRegistry


SYSTEM_PROMPT = """
You are Vastukaar, an AI software engineering agent.

You can inspect a software repository using the available tools.

Instructions:
1. Use the available tools when repository information is needed.
2. Never claim to have inspected a file unless you have actually read it.
3. Base your conclusions on the information returned by tools.
4. If a tool fails, examine the error and decide whether another
   approach is appropriate.
5. Do not invent files, functions, or repository contents.
6. Provide a clear final response when the task is complete.
"""

class AgentExecutionLimitError(Exception):
    """Raised when the agent exceeds its maximum execution iterations."""


class Agent:

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 10
    ):

        if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
            raise TypeError("max_iterations must be an integer.")

        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    def run(self, user_input: str) -> str | None:

        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("User input must be a non-empty string.")

        # Step 1: Initialise conversation history.
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        # Step 2: Start the bounded orchestration loop.
        for iteration in range(self.max_iterations):

            response = self.llm_provider.generate(
                messages=messages,
                tools=TOOLS
            )

            # print(f"\n[DEBUG] Agent iteration: {iteration + 1}")
            # print(f"[DEBUG] Tool calls: {len(response.tool_calls)}")

            # for tool_call in response.tool_calls:
            #     print(f"[DEBUG] Requested tool: {tool_call.name}")
            #     print(f"[DEBUG] Arguments: {tool_call.arguments}")

            # if response.content:
            #     print(f"[DEBUG] Response: {response.content[:300]}")

            # Step 3: Check whether the LLM has finished.
            if not response.tool_calls:
                return response.content

            # Step 4: Record the assistant's tool-call request.
            assistant_tool_calls = []

            for tool_call in response.tool_calls:
                assistant_tool_calls.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments)
                        }
                    }
                )

            assistant_message = {
                "role": "assistant",
                "tool_calls": assistant_tool_calls
            }

            if response.content is not None:
                assistant_message["content"] = response.content

            messages.append(assistant_message)

            # Step 5: Execute the requested tools.
            for tool_call in response.tool_calls:

                try:
                    result = self.tool_registry.execute_tool(
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments
                    )

                except Exception as exc:
                    # Return execution errors to the LLM so it can
                    # potentially correct its request.
                    result = {
                        "error": type(exc).__name__,
                        "message": str(exc)
                    }

                # Step 6: Return the result against its original tool-call ID.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str
                        )
                    }
                )

        # Step 7: Stop if the execution budget is exhausted.
        raise AgentExecutionLimitError(
            f"Agent exceeded its maximum of {self.max_iterations} "
            "LLM iterations without producing a final response."
        )
