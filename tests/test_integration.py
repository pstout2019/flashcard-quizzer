"""Integration tests for the full quiz application."""

import json
from pathlib import Path

import pytest

from data_loader import load_deck
from main import main
from quiz_engine import QuizSession, SequentialMode
from ui import QuizUI, run_quiz


class TestFullSession:
    """Test a complete quiz session."""

    def test_full_session(self, tmp_path: Path) -> None:
        """Run a complete quiz with correct, wrong, and case-varied answers."""
        deck_file = tmp_path / "test_deck.json"
        deck_data = [
            {"front": "Q1", "back": "Answer A"},
            {"front": "Q2", "back": "Answer B"},
            {"front": "Q3", "back": "Answer C"},
        ]
        deck_file.write_text(json.dumps(deck_data))

        deck = load_deck(deck_file)
        input_calls = [
            "Answer A",  # correct
            "wrong",  # incorrect
            "  ANSWER C  ",  # correct (case/space insensitive)
        ]
        input_iter = iter(input_calls)

        def input_fn(prompt: str = "") -> str:
            return next(input_iter)

        output_lines: list[str] = []

        def output_fn(x: str) -> None:
            output_lines.append(x)

        mode = SequentialMode(deck)
        session = QuizSession(mode)
        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)

        run_quiz(session, ui)

        assert session.stats.total_questions == 3
        assert session.stats.correct == 2
        assert session.stats.accuracy_percent == 66.7
        assert session.stats.missed_terms == ["Q2"]

        summary_text = "\n".join(output_lines)
        assert "Total Questions: 3" in summary_text
        assert "Correct: 2" in summary_text
        assert "Accuracy %: 66.7" in summary_text


class TestMainIntegration:
    """Integration tests for main.py."""

    def test_main_help(self) -> None:
        """--help exits 0 and shows help text."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_main_missing_file(
        self, capsys: "pytest.CaptureFixture[str]"
    ) -> None:
        """Missing file returns 1 with Error message on stderr."""
        result = main(["-f", "nonexistent.json"])
        assert result == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "nonexistent.json" in captured.err
        assert "Traceback" not in captured.err

    def test_main_invalid_json(
        self, tmp_path: Path, capsys: "pytest.CaptureFixture[str]"
    ) -> None:
        """Invalid JSON returns 1 with Error message on stderr."""
        deck_file = tmp_path / "bad.json"
        deck_file.write_text("[invalid json]")

        result = main(["-f", str(deck_file)])
        assert result == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Traceback" not in captured.err

    def test_main_one_question_exit(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
        capsys: "pytest.CaptureFixture[str]",
    ) -> None:
        """Typing 'exit' after one question shows summary and returns 0."""
        deck_file = tmp_path / "test.json"
        deck_data = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2", "back": "A2"},
        ]
        deck_file.write_text(json.dumps(deck_data))

        input_calls = ["A1", "exit"]
        input_iter = iter(input_calls)

        def mock_input(prompt: str = "") -> str:
            return next(input_iter)

        monkeypatch.setattr("builtins.input", mock_input)

        result = main(["-f", str(deck_file), "--no-color"])
        assert result == 0

        captured = capsys.readouterr()
        assert captured.out.count("Correct!") == 1
        assert captured.out.count("Question 2: Q2") == 1
        assert "Quiz Summary" in captured.out
        assert "Total Questions: 1" in captured.out
        assert "Correct: 1" in captured.out

    def test_main_keyboard_interrupt(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
        capsys: "pytest.CaptureFixture[str]",
    ) -> None:
        """KeyboardInterrupt (Ctrl+C) ends cleanly with summary."""
        deck_file = tmp_path / "test.json"
        deck_data = [{"front": "Q1", "back": "A1"}]
        deck_file.write_text(json.dumps(deck_data))

        def raise_keyboard_interrupt(prompt: str = "") -> str:
            raise KeyboardInterrupt()

        monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)

        result = main(["-f", str(deck_file), "--no-color"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Quiz Summary" in captured.out
        assert "Total Questions: 0" in captured.out
        assert "Traceback" not in captured.out
        assert "Traceback" not in captured.err

    def test_main_eof_error(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
        capsys: "pytest.CaptureFixture[str]",
    ) -> None:
        """EOFError (Ctrl+D) ends cleanly with summary."""
        deck_file = tmp_path / "test.json"
        deck_data = [{"front": "Q1", "back": "A1"}]
        deck_file.write_text(json.dumps(deck_data))

        def raise_eof(prompt: str = "") -> str:
            raise EOFError()

        monkeypatch.setattr("builtins.input", raise_eof)

        result = main(["-f", str(deck_file), "--no-color"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Quiz Summary" in captured.out
        assert "Total Questions: 0" in captured.out
        assert "Traceback" not in captured.out
        assert "Traceback" not in captured.err

    def test_main_adaptive_mode(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
        capsys: "pytest.CaptureFixture[str]",
    ) -> None:
        """Adaptive mode re-asks missed cards."""
        deck_file = tmp_path / "test.json"
        deck_data = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2", "back": "A2"},
            {"front": "Q3", "back": "A3"},
        ]
        deck_file.write_text(json.dumps(deck_data))

        input_calls = ["wrong", "A2", "A3", "A1"]
        input_iter = iter(input_calls)

        def mock_input(prompt: str = "") -> str:
            return next(input_iter)

        monkeypatch.setattr("builtins.input", mock_input)

        result = main(["-f", str(deck_file), "-m", "adaptive", "--no-color"])
        assert result == 0

        captured = capsys.readouterr()
        lines = captured.out.split("\n")
        question_lines = [
            line for line in lines if line.startswith("Question")
        ]
        assert question_lines == [
            "Question 1: Q1",
            "Question 2: Q2",
            "Question 3: Q3",
            "Question 4: Q1",
        ]
        assert "Total Questions: 4" in captured.out
        assert "Correct: 3" in captured.out
        assert "Missed Terms: Q1" in captured.out

    def test_main_stats_flag(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
        capsys: "pytest.CaptureFixture[str]",
    ) -> None:
        """--stats flag includes per-card statistics in summary."""
        deck_file = tmp_path / "test.json"
        deck_data = [{"front": "Card Q", "back": "Answer A"}]
        deck_file.write_text(json.dumps(deck_data))

        def mock_input(prompt: str = "") -> str:
            return "Answer A"

        monkeypatch.setattr("builtins.input", mock_input)

        result = main(["-f", str(deck_file), "--stats", "--no-color"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Per-Card Statistics" in captured.out
        lines = captured.out.split("\n")
        card_rows = [line for line in lines if line.startswith("Card Q")]
        assert len(card_rows) == 1
        row = card_rows[0]
        fields = row.split()
        assert fields[-2:] == ["1", "1"]
        assert fields[0] == "Card"
        assert fields[1] == "Q"

    def test_main_unknown_mode(self, tmp_path: Path) -> None:
        """Unknown mode exits with argparse error (exit code 2)."""
        deck_file = tmp_path / "test.json"
        deck_data = [{"front": "Q1", "back": "A1"}]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(SystemExit) as exc_info:
            main(["-f", str(deck_file), "-m", "unknown"])

        assert exc_info.value.code == 2
