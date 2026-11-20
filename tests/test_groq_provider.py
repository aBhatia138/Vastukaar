from unittest.mock import Mock, patch

from src.llm.groq_provider import GroqProvider
from src.llm.models import LLMResponse

@patch("src.llm.groq_provider.Groq")
def test_groq_provider_generate_response(mock_groq):

    #Mocking a groq client
    mock_client = Mock()
    mock_groq.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                content="Hello from Groq",
                tool_calls=None
            )
        )
    ]

    mock_client.chat.completions.create.return_value = mock_response

    messages = [
        {
            "role": "user",
            "content": "hello"
        }
    ]

    provider = GroqProvider(
        api_key="test-api-key",
        model="openai/gpt-oss-120b"
    )

    result = provider.generate(messages)

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Groq"
    assert result.tool_calls == []

    mock_groq.assert_called_once_with(
        api_key="test-api-key"
    )

    mock_client.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.3,
        max_tokens=1500
    )

@patch("src.llm.groq_provider.Groq")
def test_groq_provider_converts_tool_call_response(mock_groq):

    #Mocking a groq client
    mock_client = Mock()
    mock_groq.return_value = mock_client

    #Constructing a groq tool call in Groq's native response format
    mock_function = Mock()
    mock_function.name = "percentage_calculator"
    mock_function.arguments = '{"value": 800, "percentage": 25}'

    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function = mock_function

    #A tool call response may have no text content 
    mock_message = Mock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_response = Mock()
    mock_response.choices = [Mock(message=mock_message)]

    mock_client.chat.completions.create.return_value = mock_response

    #Input to our provider 
    messages = [
        {
            "role": "user",
            "content": "Calculate 25% of 800"
        }
    ]

    tool_defintions = [
        {
            "type": "function",
            "function": {
                "name": "percentage_calculator"
            }
        }
    ]

    #Act: Call our provider with tool defintions
    provider = GroqProvider(
        api_key="test-api-key",
        model="openai/gpt-oss-120b"
    )

    result = provider.generate(
        messages,
        tools=tool_defintions
    )

    #Assert: verify the normalized response
    assert isinstance(result, LLMResponse)
    assert result.content is None
    assert len(result.tool_calls) == 1

    tool_call = result.tool_calls[0]

    assert tool_call.id == "call_123"
    assert tool_call.name == "percentage_calculator"
    assert tool_call.arguments == {
        "value": 800,
        "percentage": 25
    }

    #Verify that the provider passed the tools to Groq 
    mock_client.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.3,
        max_tokens=1500,
        tools=tool_defintions
    )


