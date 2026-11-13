import os 
from dotenv import load_dotenv

def load_config() -> dict[str, str]:

    #Load variables from the dotenv file
    load_dotenv()

    #Read the provider selection
    provider = os.getenv("LLM_PROVIDER")

    if not provider:
        raise ValueError(
            "LLM_PROVIDER is missing from the environment. "
        )

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY could not be found in the environment. "
            )

        if not model:
            raise ValueError(
                "GROQ_MODEL could not be found in the environment. "
            )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )

    #Return the configuration in a standard structure
    return {
        "provider": provider,
        "api_key": api_key,
        "model": model
    }