LIST_DIRECTORY_TOOL = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": (
            "List the files and subdirectories inside "
            "the repository workspace. Use this tool "
            "to explore the repository structure. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": (
                        "Path of the directory relative "
                        "to the repository root. Defaults "
                        "to '.' for the repository root. "
                    )
                }
            },
            "required": [],
            "additionalProperties": False
        }
    }
}

READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the text content of a file "
            "within the repository workspace. "
            "Use this tool when you need to inspect "
            "the source code or configuration. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": (
                        "Path of the file relative to the "
                        "repository root. "
                    )
                }
            },
            "required": ["relative_path"],
            "additionalProperties": False
        }
    }
}

SEARCH_FILES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_files",
        "description": (
            "Search text files recursively within the "
            "given repository for a specified text or "
            "code fragment. This search is case-insensitive. "
            "Returns matching file paths, line numbers and "
            "matching lines. "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Text or code fragment to search for. "
                    )
                },
                "relative_path": {
                    "type": "string",
                    "description": (
                        "Directory to search, relative to the "
                        "repository root. Defaults to '.'."
                    )
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": (
                        "Maximum number of matching lines "
                        "to return. Defaults to 100. "
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}

TOOLS = [
    LIST_DIRECTORY_TOOL,
    READ_FILE_TOOL,
    SEARCH_FILES_TOOL
]