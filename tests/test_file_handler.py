"""Tests for the file handler utility module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.file_handler import FileHandlerError, read_text_file


class TestReadTextFileSuccess:
    """Tests for successful file reading."""

    def test_read_valid_text_file(self, tmp_path: Path) -> None:
        """Read a valid UTF-8 text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!", encoding="utf-8")

        result = read_text_file(test_file)

        assert result == "Hello, world!"

    def test_read_file_with_path_object(self, tmp_path: Path) -> None:
        """Accept Path object as parameter."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        result = read_text_file(test_file)

        assert result == "content"

    def test_read_file_with_string_path(self, tmp_path: Path) -> None:
        """Accept string path as parameter."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        result = read_text_file(str(test_file))

        assert result == "content"


class TestReadTextFileErrors:
    """Tests for error conditions."""

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Missing file raises FileHandlerError."""
        with pytest.raises(FileHandlerError) as exc_info:
            read_text_file(tmp_path / "nonexistent.txt")

        assert "not found" in str(exc_info.value).lower()

    def test_directory_path_raises_error(self, tmp_path: Path) -> None:
        """Directory path raises FileHandlerError."""
        with pytest.raises(FileHandlerError) as exc_info:
            read_text_file(tmp_path)

        error_msg = str(exc_info.value)
        assert "directory" in error_msg.lower()
        assert str(tmp_path) in error_msg

    def test_invalid_utf8_raises_error(self, tmp_path: Path) -> None:
        """File with invalid UTF-8 raises FileHandlerError."""
        test_file = tmp_path / "bad.txt"
        test_file.write_bytes(b"\x80\x81\x82")

        with pytest.raises(FileHandlerError) as exc_info:
            read_text_file(test_file)

        error_msg = str(exc_info.value)
        assert "utf-8" in error_msg.lower()
        assert str(test_file) in error_msg

    @pytest.mark.skipif(
        os.geteuid() == 0, reason="cannot test permissions as root"
    )
    def test_permission_denied_raises_error(self, tmp_path: Path) -> None:
        """File without read permission raises FileHandlerError."""
        test_file = tmp_path / "noperm.txt"
        test_file.write_text("content", encoding="utf-8")
        test_file.chmod(0o000)

        try:
            with pytest.raises(FileHandlerError) as exc_info:
                read_text_file(test_file)

            error_msg = str(exc_info.value)
            assert "permission" in error_msg.lower()
            assert str(test_file) in error_msg
        finally:
            test_file.chmod(0o644)

    def test_os_error_via_monkeypatch(self, tmp_path: Path) -> None:
        """Generic OSError is caught and re-raised as FileHandlerError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        with patch.object(
            Path, "read_text", side_effect=OSError("Mocked OS error")
        ):
            with pytest.raises(FileHandlerError) as exc_info:
                read_text_file(test_file)

            error_msg = str(exc_info.value)
            assert "error reading file" in error_msg.lower()


class TestErrorMessageQuality:
    """Tests for error message clarity."""

    def test_error_message_includes_filename(self, tmp_path: Path) -> None:
        """FileHandlerError message includes the filename."""
        with pytest.raises(FileHandlerError) as exc_info:
            read_text_file(tmp_path / "my_file.txt")

        assert "my_file.txt" in str(exc_info.value)
