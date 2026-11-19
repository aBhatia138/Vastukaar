
from pathlib import Path
import os


EXCLUDED_DIRECTORIES = frozenset({
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
})

SENSITIVE_FILENAMES = frozenset({
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials",
    ".netrc",
})

SENSITIVE_SUFFIXES = frozenset({
    ".key",
    ".p12",
    ".pfx",
})


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

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a path and ensure it remains inside the workspace."""

        target_path = (
            self.workspace_root / relative_path
        ).resolve(strict=False)

        try:
            target_path.relative_to(self.workspace_root)

        except ValueError:
            raise PermissionError(
                "Access outside the workspace is not permitted."
            )

        if not target_path.exists():
            raise FileNotFoundError(
                f"Path does not exist: {relative_path}"
            )

        return target_path

    def _is_excluded_directory_path(self, path: Path) -> bool:
        """Check whether a path is inside an excluded directory."""

        relative_path = path.relative_to(self.workspace_root)

        return any(
            part.casefold() in EXCLUDED_DIRECTORIES
            for part in relative_path.parts
        )

    def _is_sensitive_file(self, path: Path) -> bool:
        """Identify files that may contain credentials or private keys."""

        filename = path.name.casefold()
        suffix = path.suffix.casefold()

        # Allow the example file because it should contain placeholders.
        if filename == ".env.example":
            return False

        # Block .env and environment-specific variants.
        if filename == ".env" or filename.startswith(".env."):
            return True

        if filename in SENSITIVE_FILENAMES:
            return True

        if suffix in SENSITIVE_SUFFIXES:
            return True

        return False

    def _ensure_path_is_accessible(self, path: Path) -> None:
        """Enforce directory and sensitive-file access restrictions."""

        if self._is_excluded_directory_path(path):
            raise PermissionError(
                "Access to generated or internal directories is not permitted."
            )

        if self._is_sensitive_file(path):
            raise PermissionError(
                "Access to sensitive files is not permitted."
            )

    def list_directory(self, relative_path: str = ".") -> list[dict]:
        """List the immediate contents of an accessible directory."""

        directory = self._resolve_path(relative_path)
        self._ensure_path_is_accessible(directory)

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {relative_path}"
            )

        entries = []

        for entry in sorted(directory.iterdir()):

            # Do not expose generated directories.
            if entry.is_dir() and entry.name.casefold() in EXCLUDED_DIRECTORIES:
                continue

            # Do not expose sensitive files.
            if entry.is_file() and self._is_sensitive_file(entry):
                continue

            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file"
            })

        return entries

    def read_file(self, relative_path: str) -> str:
        """Read an accessible UTF-8 text file inside the workspace."""

        file_path = self._resolve_path(relative_path)
        self._ensure_path_is_accessible(file_path)

        if not file_path.is_file():
            raise IsADirectoryError(
                f"Not a file: {file_path}"
            )

        max_file_size = 1_000_000

        if file_path.stat().st_size > max_file_size:
            raise ValueError(
                "File is too large to read (maximum 1 MB)."
            )

        return file_path.read_text(encoding="utf-8")

    def search_files(
        self,
        query: str,
        relative_path: str = ".",
        max_results: int = 100
    ) -> list[dict]:
        """Search accessible repository text files for a query."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise TypeError(
                "max_results must be an integer."
            )

        if max_results < 1:
            raise ValueError(
                "max_results must be at least 1."
            )

        # Enforce an upper bound to prevent excessively large results.
        max_results = min(max_results, 500)

        search_directory = self._resolve_path(relative_path)
        self._ensure_path_is_accessible(search_directory)

        if not search_directory.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {relative_path}"
            )

        query = query.casefold()
        matches = []
        max_file_size = 1_000_000

        for current_root, directories, filenames in os.walk(
            search_directory,
            followlinks=False
        ):
            # Prevent traversal into generated directories.
            directories[:] = sorted(
                directory
                for directory in directories
                if directory.casefold() not in EXCLUDED_DIRECTORIES
            )

            for filename in sorted(filenames):

                candidate = Path(current_root) / filename

                try:
                    file_path = self._resolve_path(
                        candidate.relative_to(
                            self.workspace_root
                        ).as_posix()
                    )

                    self._ensure_path_is_accessible(file_path)

                except (PermissionError, FileNotFoundError):
                    continue

                if not file_path.is_file():
                    continue

                try:
                    if file_path.stat().st_size > max_file_size:
                        continue

                    file_bytes = file_path.read_bytes()

                    # Skip likely binary files.
                    if b"\x00" in file_bytes:
                        continue

                    content = file_bytes.decode("utf-8")

                except (OSError, UnicodeDecodeError):
                    continue

                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1
                ):
                    if query in line.casefold():

                        matches.append({
                            "file": file_path.relative_to(
                                self.workspace_root
                            ).as_posix(),
                            "line_number": line_number,
                            "line": line.strip()
                        })

                        if len(matches) >= max_results:
                            return matches

        return matches
