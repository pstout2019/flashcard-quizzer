"""Tests for the terminal user interface."""

from unittest.mock import MagicMock

from data_loader import Flashcard
from quiz_engine import QuizSession, SequentialMode
from ui import GREEN, RED, QuizUI, colorize, run_quiz


class TestColorize:
    """Tests for the colorize function."""

    def test_colorize_enabled(self) -> None:
        """Colorize adds ANSI codes when enabled."""
        result = colorize("hello", GREEN, True)
        assert GREEN in result
        assert "hello" in result
        assert "\033[0m" in result

    def test_colorize_disabled(self) -> None:
        """Colorize returns plain text when disabled."""
        result = colorize("hello", GREEN, False)
        assert GREEN not in result
        assert result == "hello"


class TestQuizUI:
    """Tests for the QuizUI class."""

    def test_ask_valid_answer(self) -> None:
        """ask returns the user's answer."""
        card = Flashcard(front="Q1", back="A1")
        input_fn = MagicMock(return_value="user answer")
        output_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        result = ui.ask(card, 1)

        assert result == "user answer"
        output_fn.assert_called_once()
        assert "Question 1: Q1" in output_fn.call_args[0][0]

    def test_ask_blank_answer_reprompts(self) -> None:
        """ask re-prompts on blank answers without counting them."""
        card = Flashcard(front="Q1", back="A1")
        input_fn = MagicMock(side_effect=["", "  ", "valid answer"])
        output_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        result = ui.ask(card, 1)

        assert result == "valid answer"
        assert input_fn.call_count == 3

    def test_ask_exit_command(self) -> None:
        """ask returns None when user types exit (case-insensitive)."""
        card = Flashcard(front="Q1", back="A1")

        for exit_cmd in ["exit", "EXIT", "  Exit  "]:
            input_fn = MagicMock(return_value=exit_cmd)
            output_fn = MagicMock()
            ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
            result = ui.ask(card, 1)
            assert result is None

    def test_ask_keyboard_interrupt(self) -> None:
        """ask returns None on KeyboardInterrupt."""
        card = Flashcard(front="Q1", back="A1")
        input_fn = MagicMock(side_effect=KeyboardInterrupt())
        output_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        result = ui.ask(card, 1)

        assert result is None

    def test_ask_eof_error(self) -> None:
        """ask returns None on EOFError."""
        card = Flashcard(front="Q1", back="A1")
        input_fn = MagicMock(side_effect=EOFError())
        output_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        result = ui.ask(card, 1)

        assert result is None

    def test_show_feedback_correct(self) -> None:
        """show_feedback shows green 'Correct!' for correct answers."""
        card = Flashcard(front="Q1", back="A1")
        output_fn = MagicMock()

        ui = QuizUI(output_fn=output_fn, use_color=True)
        ui.show_feedback(True, card)

        output_fn.assert_called_once()
        output = output_fn.call_args[0][0]
        assert GREEN in output
        assert "Correct!" in output

    def test_show_feedback_incorrect(self) -> None:
        """show_feedback shows red message for incorrect answers."""
        card = Flashcard(front="Q1", back="Correct Answer")
        output_fn = MagicMock()

        ui = QuizUI(output_fn=output_fn, use_color=True)
        ui.show_feedback(False, card)

        output_fn.assert_called_once()
        output = output_fn.call_args[0][0]
        assert RED in output
        assert "Incorrect" in output
        assert "Correct Answer" in output

    def test_show_feedback_no_color(self) -> None:
        """show_feedback omits ANSI codes when use_color is False."""
        card = Flashcard(front="Q1", back="A1")
        output_fn = MagicMock()

        ui = QuizUI(output_fn=output_fn, use_color=False)
        ui.show_feedback(True, card)

        output = output_fn.call_args[0][0]
        assert GREEN not in output

    def test_show_summary_basic(self) -> None:
        """show_summary displays quiz results."""
        output_fn = MagicMock()
        input_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        mode = SequentialMode(
            [
                Flashcard(front="Q1", back="A1"),
                Flashcard(front="Q2", back="A2"),
            ]
        )
        session = QuizSession(mode)
        card1 = session.next_card()
        assert card1 is not None
        session.submit_answer(card1, "A1")
        card2 = session.next_card()
        assert card2 is not None
        session.submit_answer(card2, "wrong")

        ui.show_summary(session.stats)

        all_output = "".join(str(call) for call in output_fn.call_args_list)
        assert "Total Questions" in all_output
        assert "Accuracy %" in all_output

    def test_show_summary_with_details(self) -> None:
        """show_summary shows per-card table with show_details=True."""
        output_fn = MagicMock()
        input_fn = MagicMock()

        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)
        mode = SequentialMode([Flashcard(front="Card Q", back="Answer A")])
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None
        session.submit_answer(card, "Answer A")

        ui.show_summary(session.stats, show_details=True)

        all_output = "".join(str(call) for call in output_fn.call_args_list)
        assert "Per-Card Statistics" in all_output
        assert "Card Q" in all_output

    def test_show_summary_no_missed_terms(self) -> None:
        """show_summary shows 'None' for missed terms when empty."""
        output_fn = MagicMock()

        ui = QuizUI(output_fn=output_fn)
        mode = SequentialMode([Flashcard(front="Q1", back="A1")])
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None
        session.submit_answer(card, "A1")

        ui.show_summary(session.stats)

        all_output = "".join(str(call) for call in output_fn.call_args_list)
        assert "Missed Terms: None" in all_output


class TestRunQuiz:
    """Tests for the run_quiz function."""

    def test_run_quiz_completes(self) -> None:
        """run_quiz runs through all cards and shows summary."""
        input_fn = MagicMock(side_effect=["A1", "A2", "A3"])
        output_fn = MagicMock()

        deck = [
            Flashcard(front="Q1", back="A1"),
            Flashcard(front="Q2", back="A2"),
            Flashcard(front="Q3", back="A3"),
        ]
        mode = SequentialMode(deck)
        session = QuizSession(mode)
        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)

        stats = run_quiz(session, ui)

        assert stats.total_questions == 3
        assert stats.correct == 3

    def test_run_quiz_early_exit(self) -> None:
        """run_quiz exits early with 'exit' and shows summary."""
        input_fn = MagicMock(side_effect=["A1", "exit"])
        output_fn = MagicMock()

        deck = [
            Flashcard(front="Q1", back="A1"),
            Flashcard(front="Q2", back="A2"),
        ]
        mode = SequentialMode(deck)
        session = QuizSession(mode)
        ui = QuizUI(input_fn=input_fn, output_fn=output_fn)

        stats = run_quiz(session, ui)

        assert stats.total_questions == 1
        all_output = "".join(str(call) for call in output_fn.call_args_list)
        assert "Quiz Summary" in all_output
