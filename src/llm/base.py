#Define the contract that every LLM provider must follow

from abc import ABC, abstractmethod
from src.llm.models import LLMResponse

class LLMProvider(ABC):

    @abstractmethod
    def generate(self, messages: list[dict],
                 tools: list[dict] | None = None) -> LLMResponse:
        pass