import pytest 
from jsonschema.exceptions import ValidationError

from src.tools.repository import RepositoryTools
from src.tools.registry import ToolRegistry

@pytest.fixture
def tool_registry(tmp_path):
    #Create a small temporary repo for testing
    (tmp_path / "README.md").write_text(
        "Vastukaar uses GroqProvider.",
        encoding="utf-8"
    )

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    (source_directory / "main.py").write_text(
        "class GroqProvider:\n    pass\n",
        encoding="utf-8"
    )

    repository_tools = RepositoryTools(str(tmp_path))

    return ToolRegistry(repository_tools)

def test_registry_executes_list_directory(tool_registry: ToolRegistry):
    result = tool_registry.execute_tool(
        "list_directory",
        {}
    )

    assert {"name": "README.md", "type": "file"} in result

def test_registry_executes_read_files(tool_registry: ToolRegistry):
    result = tool_registry.execute_tool(
        "read_file",
        {"relative_path": "README.md"}
    )

    assert "Vastukaar uses GroqProvider." in result

def test_registry_executes_search_files(tool_registry: ToolRegistry):
    result = tool_registry.execute_tool(
        "search_files",
        {"query": "GroqProvider"}
    )

    assert len(result) == 2

def test_registry_rejects_unknown_tool(tool_registry: ToolRegistry):
    with pytest.raises(ValueError, match="Unknown tool"):
        tool_registry.execute_tool(
            "delete_all_files",
            {}
        )

def test_registry_rejects_missing_required_arguments(tool_registry: ToolRegistry):
    with pytest.raises(ValidationError) as exc_info:
        tool_registry.execute_tool("read_file", {})

    assert "'relative_path' is a required property" in str(exc_info.value)

def test_registry_rejects_additional_arguments(tool_registry: ToolRegistry):
    with pytest.raises(ValidationError):
        tool_registry.execute_tool(
            "read_file",
            {
                "relative_path": "README.md",
                "force": True
            }
        )

def test_registry_rejects_max_results_above_limit(tool_registry: ToolRegistry):
    with pytest.raises(ValidationError):
        tool_registry.execute_tool(
            "search_files",
            {
                "query": "GroqProvider",
                "max_results": 1000
            }
        )

def test_registry_rejects_non_dictionary_arguments(tool_registry: ToolRegistry):
    with pytest.raises(TypeError, match="dictionary"):
        tool_registry.execute_tool(
            "list_directory",
            ["README.md"]
        )

def test_registry_rejects_non_string_tool_name(tool_registry: ToolRegistry):
    with pytest.raises(TypeError, match="string"):
        tool_registry.execute_tool(
            123,
            {}
        )