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

class FakeToolRegistry:

    def __init__(self, results=None, errors=None):
        self.results = results or {}
        self.errors = errors or {}
        self.executed_calls = []

    def execute_tool(self, tool_name, arguments):
        self.executed_calls.append({
            "tool_name": tool_name,
            "arguments": arguments
        })

        if tool_name in self.errors:
            raise self.errors[tool_name]

        if tool_name not in self.results:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        return self.results[tool_name]


def test_agent_returns_final_response():

    provider = FakeLLMProvider([
        LLMResponse(
            content="Hello I am Vastukaar. ",
            tool_calls=[]
        )
    ])

    registry = FakeToolRegistry()

    agent = Agent(provider, registry)

    result = agent.run("Introduce yourself. ")

    assert result == "Hello I am Vastukaar. "
    assert len(provider.calls) == 1
    assert len(registry.executed_calls) == 0

def test_agent_executes_one_tool_call():

    provider = FakeLLMProvider([
        LLMResponse(
            content=None,
            tool_calls = [
                ToolCall(
                    id="call_001",
                    name="search_files",
                    arguments={"query": "GroqProvider"}
                )
            ]
        ),
        LLMResponse(
            content="GroqProvider was found in main.py. ",
            tool_calls=[]
        )
    ])

    registry = FakeToolRegistry(
        results={
            "search_files": [
                {
                    "file": "main.py",
                    "line": 10,
                    "content": "class GroqProvider:"
                }
            ]
        }
    )

    agent = Agent(provider, registry)

    result = agent.run("find GroqProvider.")

    assert result == "GroqProvider was found in main.py. "

    assert len(registry.executed_calls) == 1

    #Verify that the tool result was returned to the LLM
    second_request_messages = provider.calls[1]["messages"]

    assert second_request_messages[-1]["role"] == "tool"
    assert second_request_messages[-1]["tool_call_id"] == "call_001"
    assert "GroqProvider" in second_request_messages[-1]["content"]

def test_agent_executes_multiple_tool_calls():

    provider = FakeLLMProvider([
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_001",
                    name="search_files",
                    arguments={"query":"GroqProvider"}
                ),
                ToolCall(
                    id="call_002",
                    name="read_file",
                    arguments={"relative_path": "main.py"}
                )
            ]
        ),
        LLMResponse(
            content="I searched for and read the relevant file. ",
            tool_calls=[]
        )
    ])

    registry = FakeToolRegistry(
        results={
            "search_files": [{"file": "main.py"}],
            "read_file": "class GroqProvider:\n   pass"
        }
    )

    agent = Agent(provider, registry)

    result = agent.run("Find and inspect GroqProvider.")

    assert result == "I searched for and read the relevant file. "
    assert len(registry.executed_calls) == 2

    tool_messages = [
        message 
        for message in provider.calls[1]["messages"]
        if message["role"] == "tool"
    ]

    assert len(tool_messages) == 2
    assert tool_messages[0]["tool_call_id"] == "call_001"
    assert tool_messages[1]["tool_call_id"] == "call_002"

def test_agent_supports_multiple_iterations():

    provider = FakeLLMProvider([
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_001",
                    name="search_files",
                    arguments={"query": "GroqProvider"}
                )
            ]
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_002",
                    name="read_file",
                    arguments={"relative_path": "main.py"}
                )
            ]
        ),
        LLMResponse(
            content="The GroqProvider class is defined in main.py. ",
            tool_calls=[]
        )
    ])

    registry = FakeToolRegistry(
        results={
            "search_files": [{"file": "main.py"}],
            "read_file": "class GroqProvider:\n  pass"
        }
    )

    agent = Agent(provider, registry)

    result = agent.run("Find and explain groqProvider. ")

    assert result == "The GroqProvider class is defined in main.py. "
    assert len(provider.calls) == 3
    assert len(registry.executed_calls) == 2

def test_agent_returns_tool_execution_errors_to_llm():

    provider = FakeLLMProvider([
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_001",
                    name="read_file",
                    arguments={"relative_path": "missing.py"}
                )
            ]
        ),
        LLMResponse(
            content="The requested file does not exist. ",
            tool_calls=[]
        )
    ])

    registry = FakeToolRegistry(
        errors={
            "read_file": FileNotFoundError(
                "File not found. "
            )
        }
    )

    agent = Agent(provider, registry)
    result = agent.run("Read missing.py. ")

    assert result == "The requested file does not exist. "

    second_request_messages = provider.calls[1]["messages"]
    tool_result = second_request_messages[-1]

    assert tool_result["role"] == "tool"
    assert "FileNotFoundError" in tool_result["content"]
    assert "File not found. " in tool_result["content"]

def test_agent_rejects_empty_user_input():

    provider = FakeLLMProvider([])
    registry = FakeToolRegistry()

    agent = Agent(provider, registry)

    with pytest.raises(ValueError, match="non-empty"):
        agent.run("    ")

    assert len(provider.calls) == 0

def test_agent__rejects_invalid_iterations_limit():

    provider = FakeLLMProvider([])
    registry = FakeToolRegistry()

    with pytest.raises(ValueError, match="at least 1"):
        Agent(provider, registry, max_iterations=0)

    with pytest.raises(TypeError, match="integer"):
        Agent(provider, registry, max_iterations=1.5)

def test_agent_stops_when_iterations_limit_is_exceeded():

    provider = FakeLLMProvider([
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_001",
                    name="search_files",
                    arguments={"query": "first"}
                )
            ]
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="call_002",
                    name="search_files",
                    arguments={"query": "second"}
                )
            ]
        )
    ])

    registry = FakeToolRegistry(
        results={"search_files": []}
    )

    agent = Agent(
        provider,
        registry,
        max_iterations=2
    )

    with pytest.raises(AgentExecutionLimitError, match="maximum of 2"):
        agent.run("Keep searching")

    assert len(provider.calls) == 2
    assert len(registry.executed_calls) == 2