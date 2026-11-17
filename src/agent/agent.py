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
    