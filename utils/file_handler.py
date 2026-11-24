"""Utility module for safe file reading operations."""

from pathlib import Path


class FileHandlerError(Exception):
    """Exception raised when file operations fail."""

    pass


def read_text_file(path: str | Path) -> str:
    """Read a UTF-8 text file and return its contents.

    Args:
        path: Path to the file to read.

    Returns:
        The contents of the file as a string.

    Raises:
        FileHandlerError: If the file is missing, is a directory, cannot be
            read, or contains invalid UTF-8.
    """
    path_obj = Path(path)
    file_path_str = str(path_obj)

    if not path_obj.exists():
        raise FileHandlerError(f"File not found: {file_path_str}")

    if path_obj.is_dir():
        raise FileHandlerError(
            f"Path is a directory, not a file: {file_path_str}"
        )

    try:
        return path_obj.read_text(encoding="utf-8")
    except PermissionError as e:
        raise FileHandlerError(
            f"Permission denied reading file: {file_path_str}"
        ) from e
    except UnicodeDecodeError as e:
        raise FileHandlerError(
            f"File contains invalid UTF-8: {file_path_str}"
        ) from e
    except OSError as e:
        raise FileHandlerError(f"Error reading file: {file_path_str}") from e
