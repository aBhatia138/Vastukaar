from unittest.mock import Mock, patch
import pytest
from src.llm.factory import createProvider

@patch("src.llm.factory.GroqProvider")
def test_factory_creates_groq_provider(mock_groq_provider):

    config = {
        "provider": "groq",
        "api_key": "test-api-key",
        "model": "openai/gpt-oss-120b"
    }

    expected_provider = Mock()
    mock_groq_provider.return_value = expected_provider

    provider = createProvider(config)

    assert provider is expected_provider

    mock_groq_provider.assert_called_once_with(
        api_key="test-api-key",
        model="openai/gpt-oss-120b"
    )

def test_factory_rejects_unsupported_llm_provider():

    config = {
        "provider": "unsupported",
        "api_key": "test-api-key",
        "model": "some-model"
    }

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        createProvider(config)