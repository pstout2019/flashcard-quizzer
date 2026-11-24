"""Quiz engine with mode strategies and session management."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence, Type

from data_loader import Flashcard

RETRY_GAP = 2
MAX_RETRIES = 3


class UnknownModeError(ValueError):
    """Exception raised when an unknown quiz mode is requested."""

    pass


class QuizMode(ABC):
    """Abstract base class for quiz mode strategies.

    Defines the interface for different card-selection strategies. Subclasses
    must implement next_card() to provide cards in their respective order.
    """

    def __init__(
        self,
        cards: Sequence[Flashcard],
        rng: random.Random | None = None,
    ) -> None:
        """Initialize a quiz mode.

        Args:
            cards: A sequence of Flashcard objects to quiz on.
            rng: Optional Random instance (unused in base class).

        Raises:
            ValueError: If the sequence is empty.
        """
        if not cards:
            raise ValueError("Cannot create a quiz mode with an empty deck")
        self._cards = list(cards)

    @abstractmethod
    def next_card(self) -> Flashcard | None:
        """Get the next card to ask, or None if the quiz is complete.

        Returns:
            The next Flashcard to ask, or None when no more cards remain.
        """

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record the result of an answer (hook for subclass use).

        Args:
            card: The Flashcard that was answered.
            correct: True if the answer was correct, False otherwise.
        """


class SequentialMode(QuizMode):
    """Quiz mode that presents cards in file order, once each."""

    def __init__(
        self,
        cards: Sequence[Flashcard],
        rng: random.Random | None = None,
    ) -> None:
        """Initialize sequential mode.

        Args:
            cards: A sequence of Flashcard objects.
            rng: Optional Random instance (unused).

        Raises:
            ValueError: If the sequence is empty.
        """
        super().__init__(cards, rng=rng)
        self._index = 0

    def next_card(self) -> Flashcard | None:
        """Get the next card in sequence.

        Returns:
            The next Flashcard, or None when the deck is exhausted.
        """
        if self._index >= len(self._cards):
            return None
        card = self._cards[self._index]
        self._index += 1
        return card


class RandomMode(QuizMode):
    """Quiz mode that presents cards in random order, once each."""

    def __init__(
        self,
        cards: Sequence[Flashcard],
        rng: random.Random | None = None,
    ) -> None:
        """Initialize random mode.

        Args:
            cards: A sequence of Flashcard objects.
            rng: Optional Random instance for seeded shuffling (for tests).
                Defaults to the global random module.

        Raises:
            ValueError: If the sequence is empty.
        """
        super().__init__(cards, rng=rng)
        self._rng = rng if rng is not None else random
        self._shuffled = list(self._cards)
        self._rng.shuffle(self._shuffled)
        self._index = 0

    def next_card(self) -> Flashcard | None:
        """Get the next card in random order.

        Returns:
            The next Flashcard, or None when the deck is exhausted.
        """
        if self._index >= len(self._shuffled):
            return None
        card = self._shuffled[self._index]
        self._index += 1
        return card


class AdaptiveMode(QuizMode):
    """Quiz mode with adaptive retry logic for missed cards.

    Cards are initially presented in file order. When answered incorrectly,
    a card is re-queued to appear after RETRY_GAP other cards (or sooner if
    fewer remain). Each card can be re-asked at most MAX_RETRIES times.
    """

    def __init__(
        self,
        cards: Sequence[Flashcard],
        rng: random.Random | None = None,
    ) -> None:
        """Initialize adaptive mode.

        Args:
            cards: A sequence of Flashcard objects.
            rng: Optional Random instance (unused).

        Raises:
            ValueError: If the sequence is empty.
        """
        super().__init__(cards, rng=rng)
        self._main_queue: list[Flashcard] = list(self._cards)
        self._retry_queue: list[tuple[Flashcard, int]] = []

    def next_card(self) -> Flashcard | None:
        """Get the next card using adaptive retry logic.

        Returns cards from the retry queue when they are due (after RETRY_GAP
        other cards have been asked), or from the main queue otherwise.

        Returns:
            The next Flashcard, or None when no cards remain.
        """
        if not self._main_queue and not self._retry_queue:
            return None

        if self._retry_queue:
            card, gap_remaining = self._retry_queue[0]
            if gap_remaining <= 0:
                self._retry_queue.pop(0)
                return card
            self._retry_queue[0] = (card, gap_remaining - 1)

        if self._main_queue:
            return self._main_queue.pop(0)

        return None

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Handle the result of an answer, re-queueing if necessary.

        Args:
            card: The Flashcard that was answered.
            correct: True if the answer was correct, False otherwise.
        """
        if not correct:
            retry_count = sum(1 for c, _ in self._retry_queue if c == card)
            if retry_count < MAX_RETRIES:
                self._retry_queue.append((card, RETRY_GAP))


_MODE_REGISTRY: dict[str, Type[QuizMode]] = {
    "sequential": SequentialMode,
    "random": RandomMode,
    "adaptive": AdaptiveMode,
}


def create_quiz_mode(
    name: str,
    cards: Sequence[Flashcard],
    rng: random.Random | None = None,
) -> QuizMode:
    """Create a quiz mode instance by name.

    Args:
        name: The name of the mode ("sequential", "random", or "adaptive").
            Case-insensitive and whitespace-trimmed.
        cards: A sequence of Flashcard objects for the quiz.
        rng: Optional Random instance for RandomMode seeding.

    Returns:
        An instance of the requested QuizMode.

    Raises:
        UnknownModeError: If the name does not match a registered mode.
    """
    normalized_name = name.strip().lower()

    if normalized_name not in _MODE_REGISTRY:
        valid_names = ", ".join(sorted(_MODE_REGISTRY.keys()))
        raise UnknownModeError(
            f"Unknown mode '{name}'. Valid modes: {valid_names}"
        )

    mode_class = _MODE_REGISTRY[normalized_name]
    return mode_class(cards, rng=rng)


def available_modes() -> list[str]:
    """Get the list of available quiz mode names.

    Returns:
        A sorted list of mode names that can be passed to create_quiz_mode.
    """
    return sorted(_MODE_REGISTRY.keys())


@dataclass
class SessionStats:
    """Statistics for a quiz session.

    Attributes:
        total_questions: Total number of card answers submitted (including
            retries).
        correct: Number of answers that were correct on the first try.
        missed_terms: Fronts of cards answered incorrectly at least once,
            in the order they were first missed. Contains each term once.
    """

    total_questions: int = 0
    correct: int = 0
    missed_terms: list[str] = field(default_factory=list)

    @property
    def accuracy_percent(self) -> float:
        """Calculate accuracy as a percentage.

        Returns:
            The percentage of correct answers to total questions, rounded to
            one decimal place. Returns 0.0 if no questions have been answered.
        """
        if self.total_questions == 0:
            return 0.0
        return round(100.0 * self.correct / self.total_questions, 1)


class QuizSession:
    """Manages a quiz session with a chosen mode and tracks statistics.

    Wraps a QuizMode and provides methods to get the next card, submit
    answers, and track statistics.
    """

    def __init__(self, mode: QuizMode) -> None:
        """Initialize a quiz session.

        Args:
            mode: A QuizMode instance to use for card selection.
        """
        self._mode = mode
        self._stats = SessionStats()

    def next_card(self) -> Flashcard | None:
        """Get the next card to ask.

        Returns:
            The next Flashcard to ask, or None if the quiz is complete.
        """
        return self._mode.next_card()

    def submit_answer(self, card: Flashcard, answer: str) -> bool:
        """Submit an answer to a card and update statistics.

        Answers are compared case-insensitively and after stripping
        surrounding whitespace.

        Args:
            card: The Flashcard that was asked.
            answer: The user's answer as a string.

        Returns:
            True if the answer was correct, False otherwise.
        """
        self._stats.total_questions += 1

        is_correct = answer.strip().casefold() == card.back.strip().casefold()

        if is_correct:
            self._stats.correct += 1
        else:
            if card.front not in self._stats.missed_terms:
                self._stats.missed_terms.append(card.front)

        self._mode.record_result(card, is_correct)
        return is_correct

    @property
    def stats(self) -> SessionStats:
        """Get the current session statistics.

        Returns:
            A SessionStats object with current quiz metrics.
        """
        return self._stats
