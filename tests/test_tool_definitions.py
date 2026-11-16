from src.tools.definitions import TOOLS

def test_all_repository_tools_are_defined():
    tools_names = [
        tool["function"]["name"]
        for tool in TOOLS
    ]

    assert "list_directory" in tools_names
    assert "read_file" in tools_names
    assert "search_files" in tools_names

def test_tool_names_are_unique():
    tool_names = [
        tool["function"]["name"]
        for tool in TOOLS
    ]

    assert len(tool_names) == len(set(tool_names))

def test_read_file_requires_path():
    read_file_tool = next(
        tool for tool in TOOLS
        if tool["function"]["name"] == "read_file"
    )

    parameters = read_file_tool["function"]["parameters"]

    assert "relative_path" in parameters["required"]

def test_search_files_requires_query():
    search_tool = next(
        tool for tool in TOOLS
        if tool["function"]["name"] == "search_files"
    )

    parameters = search_tool["function"]["parameters"]

    assert "query" in parameters["required"]
    assert "relative_path" not in parameters["required"]
    assert "max_results" not in parameters["required"]

def test_search_files_has_result_limits():
    search_tool = next(
        tool for tool in TOOLS
        if tool["function"]["name"] == "search_files"
    )

    properties = search_tool["function"]["parameters"]["properties"]

    assert properties["max_results"]["minimum"] == 1
    assert properties["max_results"]["maximum"] == 500

def test_all_tools_reject_additional_properties():
    for tool in TOOLS:
        parameters = tool["function"]["parameters"]

        assert parameters["additionalProperties"] is False

