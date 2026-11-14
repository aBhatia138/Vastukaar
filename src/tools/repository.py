from pathlib import Path
import os

class RepositoryTools:

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

        if not self.workspace_root.exists():
            raise FileNotFoundError(
                f"Workspace does not exist: {self.workspace_root}"
            )

        if not self.workspace_root.is_dir():
            raise NotADirectoryError(
                f"Workspace is not a directory: {self.workspace_root}"
            )

    def _resolve_path(self, realtive_path: str) -> Path:
        #Resolve a path and ensure it remains inside the workspace
        target_path = (self.workspace_root / realtive_path).resolve(strict=False)

        try:
            target_path.relative_to(self.workspace_root)

        except ValueError:
            raise PermissionError(
                "Access outside the workspace is not permitted. "
            )

        if not target_path.exists():
            raise FileNotFoundError(
                f"Path does not exist: {realtive_path}"
            )

        return target_path

    def list_directory(self, relative_path: str = ".") -> list[dict]:
        #List the immediate contents of a directory
        directory = self._resolve_path(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {relative_path}"
            )

        entries = []

        for entry in sorted(directory.iterdir()):
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file"
            })

        return entries

    def read_file(self, relative_path: str) -> str:
        #Read a UTF-8 text file inside the workspace 
        file_path = self._resolve_path(relative_path)

        if not file_path.is_file():
            raise IsADirectoryError(
                f"Not a file: {file_path}"
            )

        max_file_size = 1_000_000

        if file_path.stat().st_size > max_file_size:
            raise ValueError(
                "File is too large to read (maximum 1 MB)"
            )

        return file_path.read_text(encoding="utf-8")

    def search_files(self, query: str, relative_path: str = ".",
                     max_results: int = 100) -> list[dict]:
        #Search repo text files for a query
        #Search is recursive and case-insensitive
        #Returns: A list of dictionaries containing file, line_number and line

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Search query cannot be empty. "
            )

        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise TypeError(
                "max_results must be an integer. "
            )

        if max_results < 1:
            raise ValueError(
                "max_results must be atleast 1. "
            )

        #Enforce an upper bound to prevent exactly large results 
        max_results = min(max_results, 500)

        search_directory = self._resolve_path(relative_path)

        if not search_directory.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {relative_path}"
            )

        excluded_directories = [
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            ".pytest_cache"
        ]

        max_file_size = 1_000_000
        query = query.casefold()

        matches = []

        