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
            "content": "Explain what an AI agent is in simple terms. "
        }
    ]

    #Generate a response
    answer = provider.generate(messages)

    print("\nVastukaar response: ")
    print(answer)

if __name__ == "__main__":
    main()
