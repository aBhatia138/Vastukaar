from src.config import load_config
from src.llm.factory import createProvider

def main():

    #Load and validate the application configuration
    config = load_config()

    #Create the configured LLM provider
    provider = createProvider(config)

    #Define the conversation
    messages = [
        {
            "role": "system",
            "content": "You are Vastukaar, a helpful AI software "
                        "engineering assistant. "
        },
        {
            "role": "user",
            "content": "What is 30% of 800? "
        }
    ]

    #Generate a response
    response = provider.generate(messages)

    if response.content is not None:
        print(response.content)

    if response.tool_calls:
        print("\nTool callls requested: ")
        for tool_call in response.tool_calls:
            print(tool_call)

if __name__ == "__main__":
    main()
