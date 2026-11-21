from pathlib import Path
import sys

from src.config import load_config
from src.llm.factory import createProvider
from src.tools.repository import RepositoryTools
from src.tools.registry import ToolRegistry
from src.agent.agent import AgentExecutionLimitError, Agent
from src.agent.planner import Planner
from src.agent.orchestrator import Orchestrator

def create_orchestrator(workspace_root: Path) -> Orchestrator:

    #1. Load application configuration
    config = load_config()

    #2. Create the configured LLM Provider
    provider = createProvider(config)

    #3. Initialize repository tools for the selected workspace 
    repository_tools = RepositoryTools(workspace_root)

    #4. Register the available tools
    tool_registry = ToolRegistry(repository_tools)

    #5. Construct the agent
    agent = Agent(
        llm_provider=provider,
        tool_registry=tool_registry
    )

    #6. Construct the Planner
    planner = Planner(
        llm_provider=provider
    )

    #7. Construct the orchestrator
    orchestrator = Orchestrator(
        planner=planner,
        agent=agent,
        max_agent_calls=20
    )

    return orchestrator

def main():
    print("=" * 55)
    print("                 VASTUKAAR")
    print("       Autonomous Software Engineering Agent")
    print("=" * 55)

    # Select the repository workspace.
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

    # Construct the Orchestrator and its dependencies.
    orchestrator = create_orchestrator(workspace_root)

    # Accept a task from the user.
    user_input = input(
        "\nWhat would you like Vastukaar to do?: "
    ).strip()

    if not user_input:
        raise ValueError("Please provide a task.")

    print("\nVastukaar is planning and executing your task...\n")

    # Execute the complete task lifecycle.
    result = orchestrator.run(user_input)

    # Display the final outcome.
    print("=" * 55)
    print("             VASTUKAAR'S REPORT")
    print("=" * 55)

    print(f"\nGoal: {result.goal}")
    print(f"Status: {result.status.value}")

    print(f"\n{result.message}")

    print("\nSTEP-BY-STEP EXECUTION")
    print("-" * 55)

    for step in result.plan.steps:
        print(f"\nStep {step.id}: {step.description}")
        print(f"Status: {step.status.value}")

    print("\nEXECUTION HISTORY")
    print("-" * 55)

    for entry in result.execution_history:
        print(f"\nStep ID: {entry['step_id']}")
        print(f"Status: {entry['status']}")
        print(f"Result: {entry['result']}")

    print("\n" + "=" * 55)


if __name__ == "__main__":
    main()

