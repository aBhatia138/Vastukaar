from jsonschema import validate
from jsonschema.exceptions import ValidationError

from src.tools.definitions import TOOLS
from src.tools.repository import RepositoryTools

class ToolRegistry:

    def __init__(self, repository_tools: RepositoryTools):
        
        #Mapping explicitly the permitted tool names to their 
        #corresponding python implementations
        self._tool_functions = {
            "list_directory": repository_tools.list_directory,
            "read_file": repository_tools.read_file,
            "search_files": repository_tools.search_files
        }

        #Map the tool names to their json schema definitions
        self._tool_schemas = {
            tool["function"]["name"]: tool["function"]["parameters"]
            for tool in TOOLS
        }

        #Ensure that every registered function has a 
        #corresponding tool defintion, and vice versa
        if set(self._tool_functions) != set(self._tool_schemas):
            raise ValueError(
                "Registered tools and tool defintions don't match. "
            )

    def execute_tool(self, tool_name: str,arguments: dict):

        #Step 1: Validate the tool name
        if not isinstance(tool_name, str):
            raise TypeError(
                "Tool name must be a string. "
            )

        if tool_name not in self._tool_functions:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        #Step 2: Validate the argument's basic type
        if not isinstance(arguments, dict):
            raise TypeError(
                "Tool arguments must be a dictionary. "
            )

        #Step 3: Validate arguments against the tool's JSON schema
        schema = self._tool_schemas[tool_name]

        validate(
            instance=arguments,
            schema=schema
        )

        #Step 4: Execute the explicitly registered function
        function = self._tool_functions[tool_name]

        return function(**arguments)