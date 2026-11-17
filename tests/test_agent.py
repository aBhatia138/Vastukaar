import copy

import pytest 

from src.agent.agent import Agent, AgentExecutionLimitError
from src.llm.models import LLMResponse, ToolCall

class FakeLLMProvider:

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, messages, tools=None):
        #Save a snapshot of the conversation at this point
        self.calls.append({
            "messages": copy.deepcopy(messages),
            "tools": tools
        })

        if not self.responses:
            raise RuntimeError("No more fake LLM responses available. ")

        return self.responses.pop(0)