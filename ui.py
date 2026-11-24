"""Terminal user interface for the flashcard quiz."""

from typing import Callable, Optional

from data_loader import Flashcard
from quiz_engine import QuizSession, SessionStats

GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def colorize(text: str, color: str, enabled: bool) -> str:
    """Colorize text if colors are enabled.

    Args:
        text: The text to colorize.
        color: ANSI color code (e.g., GREEN, RED, BOLD).
        enabled: Whether to apply the color.

    Returns:
        Colorized text if enabled, otherwise the original text.
    """
    if not enabled:
        return text
    return f"{color}{text}{RESET}"


class QuizUI:
    """Terminal interface for quiz interaction."""

    def __init__(
        self,
        input_fn: Optional[Callable[[str], str]] = None,
        output_fn: Optional[Callable[[str], None]] = None,
        use_color: bool = True,
    ) -> None:
        """Initialize the quiz UI.

        Args:
            input_fn: Function to read user input (default: built-in input).
            output_fn: Function to write output (default: built-in print).
            use_color: Whether to use ANSI colors in output.
        """
        self._input = input_fn or input
        self._output = output_fn or print
        self._use_color = use_color

    def ask(self, card: Flashcard, number: int) -> Optional[str]:
        """Ask a question and get the user's answer.

        Handles exit commands, KeyboardInterrupt, and EOFError. Re-prompts
        on blank answers without counting them.

        Args:
            card: The Flashcard to ask.
            number: The question number (1-based).

        Returns:
            The user's answer, or None if they quit or hit EOF.
        """
        self._output(f"Question {number}: {card.front}")
        while True:
            try:
                answer = self._input("Your answer: ").strip()
            except (KeyboardInterrupt, EOFError):
                return None

            if answer.lower() == "exit":
                return None

            if answer:
                return answer

    def show_feedback(self, correct: bool, card: Flashcard) -> None:
        """Show feedback for an answer.

        Args:
            correct: Whether the answer was correct.
            card: The Flashcard that was answered.
        """
        if correct:
            message = "Correct!"
            colored = colorize(message, GREEN, self._use_color)
            self._output(colored)
        else:
            message = f"Incorrect. The answer is: {card.back}"
            colored = colorize(message, RED, self._use_color)
            self._output(colored)

    def show_summary(
        self, stats: SessionStats, show_details: bool = False
    ) -> None:
        """Show a summary of the quiz results.

        Args:
            stats: The session statistics.
            show_details: Whether to show per-card statistics.
        """
        self._output("\n" + "=" * 40)
        self._output("Quiz Summary")
        self._output("=" * 40)
        self._output(f"Total Questions: {stats.total_questions}")
        self._output(f"Correct: {stats.correct}")
        self._output(f"Accuracy %: {stats.accuracy_percent}")
        missed = (
            ", ".join(stats.missed_terms) if stats.missed_terms else "None"
        )
        self._output(f"Missed Terms: {missed}")

        if show_details and stats.card_attempts:
            self._output("\n" + "-" * 40)
            self._output("Per-Card Statistics")
            self._output("-" * 40)
            self._output(f"{'Card':<30} {'Attempts':<10} {'Correct':<10}")
            self._output("-" * 40)
            for front in stats.card_attempts.keys():
                attempts = stats.card_attempts[front]
                correct = stats.card_correct[front]
                self._output(f"{front:<30} {attempts:<10} {correct:<10}")


def run_quiz(
    session: QuizSession, ui: QuizUI, show_details: bool = False
) -> SessionStats:
    """Run the quiz loop.

    Args:
        session: The QuizSession to run.
        ui: The QuizUI interface.
        show_details: Whether to show per-card statistics in summary.

    Returns:
        The final SessionStats from the session.
    """
    try:
        while True:
            card = session.next_card()
            if card is None:
                break

            number = session.stats.total_questions + 1
            answer = ui.ask(card, number)
            if answer is None:
                break

            is_correct = session.submit_answer(card, answer)
            ui.show_feedback(is_correct, card)
    finally:
        ui.show_summary(session.stats, show_details)

    return session.stats
