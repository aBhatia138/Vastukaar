import pytest

from src.tools.repository import RepositoryTools

def test_search_files_finds_matching_text(tmp_path):
    source_file = tmp_path / "main.py"
    source_file.write_text(
        "import os\nclass GroqProvider:\n    pass\n",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    results = tools.search_files("GroqProvider")

    assert len(results) == 1
    assert results[0]["file"] == "main.py"
    assert results[0]["line_number"] == 2
    assert "GroqProvider" in results[0]["line"]

def test_search_files_respects_max_results(tmp_path):
    source_file = tmp_path / "main.py"
    source_file.write_text(
        "target\n"
        "target\n"
        "target\n",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    results = tools.search_files("target", max_results=2)

    assert len(results) == 2

def test_search_files_rejects_empty_query(tmp_path):
    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(ValueError):
        tools.search_files("")

def test_search_files_excludes_generated_directories(tmp_path):
    source_file = tmp_path / ".venv" / "package.py"
    source_file.parent.mkdir()
    source_file.write_text("target\n", encoding="utf-8")

    tools = RepositoryTools(str(tmp_path))

    results = tools.search_files("target")

    assert results == []