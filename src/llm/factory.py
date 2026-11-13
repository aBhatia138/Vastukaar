from src.llm.base import LLMProvider
from src.llm.groq_provider import GroqProvider

def createProvider(config: dict[str, str]) -> LLMProvider:

    provider_name = config["provider"]

    if provider_name == "groq":
        return GroqProvider(
            api_key=config["api_key"],
            model=config["model"]
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider_name}"
    )