from pathlib import Path
import sys

from src.config import load_config
from src.llm.factory import createProvider
from src.tools.repository import RepositoryTools
from src.tools.registry import ToolRegistry
from src.agent.agent import AgentExecutionLimitError, Agent

def create_agent(workspace_root: Path) -> Agent:
    #Construct Vastukaar and inject its dependencies

    #Load config
    config = load_config()

    #Create the configured LLM provider
    provider = createProvider(config)

    #Initialize repository tools for the selected workspace
    repository_tools = RepositoryTools(workspace_root)

    #Register the available tools
    tool_registry = ToolRegistry(repository_tools)

    #Construct the agent with its dependencies
    agent = Agent(
        llm_provider=provider,
        tool_registry=tool_registry
    )

    return agent

def main():

    print("=" * 55)
    print("                 VASTUKAAR")
    print("       Autonomous Software Engineering Agent")
    print("=" * 55)

    #Asking the user which repository Vastukaar should inspect
    workspace_input = (
        "\nRepository path (press Enter for current directory): "
    ).strip()

    # if workspace_input:
    #     workspace_root = Path(workspace_input).expanduser().resolve()
    # else:
    #     workspace_root = Path.cwd().resolve()

    if len(sys.argv) > 1:
        workspace_root = Path(sys.argv[1]).expanduser().resolve()
    else:
        workspace_root = Path.cwd().resolve()

    if not workspace_root.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace_root}"
        )

    if not workspace_root.is_dir():
        raise NotADirectoryError(
            f"Workspace is not a directory: {workspace_root}"
        )

    print(f"\nWorkspace: {workspace_root}")

    #Construct the agent
    agent = create_agent(workspace_root)

    #Accept a task from a user
    user_input = input(
        "\nWhat would you like Vastukaar to do?: "
    ).strip()

    if not user_input:
        raise ValueError(
            "Please provide a task. "
        )

    print("\nVastukaar is waiting....\n")

    try:
        result = agent.run(user_input)

    except AgentExecutionLimitError as e:
        print(f"Execution stopped: {e}")
        return

    print("=" * 55)
    print("VASTUKAAR'S RESPONSE")
    print("=" * 55)

    if result is not None:
        print(result)

    else:
        print("The agent has returned the response. ")

if __name__ == "__main__":
    main()