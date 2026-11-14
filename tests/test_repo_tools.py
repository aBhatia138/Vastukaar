from src.tools.repository import RepositoryTools

def test_list_directory(tmp_path):
    #Create a temporary repo
    (tmp_path / "main.py").write_text(
        "print('Hello')",
        encoding="utf-8"
    )

    (tmp_path / "tests").mkdir()

    tools = RepositoryTools(str(tmp_path))

    #Act
    result = tools.list_directory()

    #Check
    assert result == [
        {"name": "main.py","type": "file"},
        {"name": "tests", "type": "directory"}
    ]

def test_read_file(tmp_path):
    expected_content = "def hello():\n return 'world' "

    (tmp_path / "main.py").write_text(
        expected_content,
        encoding="utf-8"
    )

    tools = RepositoryTools(str(tmp_path))

    #Act
    result = tools.read_file("main.py")

    #Assert
    assert result == expected_content

def test_reject_path_outside_workspace(tmp_path):
    tools = RepositoryTools(str(tmp_path))

    #Act and assert
    try:
        tools.read_file("../../secret.txt")
        assert False, "Expected PermissionError"

    except PermissionError:
        pass

def test_reject_nonexistent_file(tmp_path):
    tools = RepositoryTools(str(tmp_path))

    try:
        tools.read_file("does_not_exist.py")
        assert False, "Expected FileNotFoundError"

    except FileNotFoundError:
        pass