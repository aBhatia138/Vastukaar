import json
from groq import Groq

from src.llm.base import LLMProvider
from src.llm.models import LLMResponse, ToolCall

class GroqProvider(LLMProvider):

    def __init__(self, api_key: str, model: str) -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResponse:
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500
        }

        if tools is not None:
            request_params["tools"] = tools

        response = self.client.chat.completions.create(
            **request_params
        )

        message = response.choices[0].message

        tool_calls = []

        if message.tool_calls:
            for tool_call in message.tool_calls:
                arguments = json.loads(
                    tool_call.function.arguments
                )

                tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=arguments
                    )
                )

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls
        )