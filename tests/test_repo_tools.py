import pytest

from src.tools.repository import RepositoryTools

def test_read_file_rejects_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=secret-value",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.read_file(".env")

def test_read_file_rejects_production_env_file(tmp_path):
    env_file = tmp_path / ".env.production"
    #It should be noted that .env.production is not present in the workspace 
    #the time this is written. This is a future check.

    env_file.write_text(
        "DATABASE_PASSWORD=secret-value",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.read_file(".env.production")

def test_read_file_allows_env_example(tmp_path):
    env_file = tmp_path / ".env.example"
    env_file.write_text(
        "GROQ_API_KEY=your-api-key-here",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    result = tools.read_file(".env.example")

    assert result == "GROQ_API_KEY=your-api-key-here"

def test_read_file_rejects_private_key_files(tmp_path):
    key_file = tmp_path / "id_rsa"
    key_file.write_text(
        "PRIVATE KEY CONTENT",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.read_file("id_rsa")

def test_read_files_rejects_key_extension(tmp_path):
    key_file = tmp_path / "server.key"
    key_file.write_text(
        "PRIVATE KEY CONTENT",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.read_file("server.key")

def test_search_files_excludes_sensitive_files(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=secret-value",
        encoding="utf-8"
    )

    source_file = tmp_path / "main.py"
    source_file.write_text(
        "class GroqProvider:\n   pass\n",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    results = tools.search_files("GROQ_API_KEY")

    assert results == []

def test_list_directory_excludes_generated_directories(tmp_path):
    generated_directories = [
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules"
    ]

    for directory in generated_directories:
        (tmp_path / directory).mkdir()

    (tmp_path / "main.py").write_text(
        "print('Hello')",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    results = tools.list_directory()

    names = {entry["name"] for entry in results}

    assert names == {"main.py"}

def test_search_files_rejects_excluded_directory_as_root(tmp_path):
    venv_directory = tmp_path / ".venv"
    venv_directory.mkdir()

    (venv_directory / "package.py").write_text(
        "target\n",
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.search_files(
            "target",
            relative_path=".venv"
        )

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