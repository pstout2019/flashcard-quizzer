"""Tests for quiz engine modes and session management."""

import random
from typing import Sequence

import pytest

from data_loader import Flashcard
from quiz_engine import (
    MAX_RETRIES,
    RETRY_GAP,
    AdaptiveMode,
    QuizModeFactory,
    QuizSession,
    RandomMode,
    SequentialMode,
    SessionStats,
    UnknownModeError,
)


@pytest.fixture
def sample_deck() -> Sequence[Flashcard]:
    """Create a small sample deck for testing."""
    return [
        Flashcard(front="What is Python?", back="A programming language"),
        Flashcard(front="What is git?", back="A version control system"),
        Flashcard(front="What is Linux?", back="An operating system"),
    ]


@pytest.fixture
def four_card_deck() -> Sequence[Flashcard]:
    """Create a 4-card deck for adaptive mode testing."""
    return [
        Flashcard(front="Card A", back="Answer A"),
        Flashcard(front="Card B", back="Answer B"),
        Flashcard(front="Card C", back="Answer C"),
        Flashcard(front="Card D", back="Answer D"),
    ]


class TestQuizModeFactory:
    """Tests for the quiz mode factory function."""

    def test_quiz_mode_factory(self, sample_deck: Sequence[Flashcard]) -> None:
        """Create each mode type using the factory."""
        sequential = QuizModeFactory.create("sequential", sample_deck)
        assert isinstance(sequential, SequentialMode)

        random_mode = QuizModeFactory.create("random", sample_deck)
        assert isinstance(random_mode, RandomMode)

        adaptive = QuizModeFactory.create("adaptive", sample_deck)
        assert isinstance(adaptive, AdaptiveMode)

    def test_factory_case_insensitive(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Mode name matching is case-insensitive."""
        mode = QuizModeFactory.create("ADAPTIVE", sample_deck)
        assert isinstance(mode, AdaptiveMode)

        mode = QuizModeFactory.create("Random", sample_deck)
        assert isinstance(mode, RandomMode)

    def test_factory_whitespace_trimmed(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Mode name whitespace is trimmed."""
        mode = QuizModeFactory.create("  adaptive  ", sample_deck)
        assert isinstance(mode, AdaptiveMode)

    def test_factory_unknown_mode(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Unknown mode name raises UnknownModeError with valid names."""
        with pytest.raises(UnknownModeError) as exc_info:
            QuizModeFactory.create("unknown", sample_deck)

        error_msg = str(exc_info.value)
        assert "unknown" in error_msg.lower()
        assert "sequential" in error_msg
        assert "random" in error_msg
        assert "adaptive" in error_msg

    def test_available_modes(self) -> None:
        """Available modes returns all registered modes."""
        modes = QuizModeFactory.available_modes()
        assert "sequential" in modes
        assert "random" in modes
        assert "adaptive" in modes


class TestSequentialMode:
    """Tests for sequential quiz mode."""

    def test_sequential_order(self, sample_deck: Sequence[Flashcard]) -> None:
        """Sequential mode returns cards in file order."""
        mode = SequentialMode(sample_deck)
        cards = []
        while True:
            card = mode.next_card()
            if card is None:
                break
            cards.append(card)

        assert len(cards) == 3
        assert cards[0].front == "What is Python?"
        assert cards[1].front == "What is git?"
        assert cards[2].front == "What is Linux?"

    def test_sequential_then_none(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Sequential mode returns None after all cards."""
        mode = SequentialMode(sample_deck)
        for _ in range(3):
            mode.next_card()
        assert mode.next_card() is None
        assert mode.next_card() is None

    def test_empty_deck_raises_error(self) -> None:
        """Empty deck raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SequentialMode([])
        assert "empty" in str(exc_info.value).lower()

    def test_does_not_mutate_input_deck(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Sequential mode does not mutate the input deck."""
        deck_list = list(sample_deck)
        mode = SequentialMode(sample_deck)
        mode.next_card()
        assert list(sample_deck) == deck_list

    def test_record_result_is_noop(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Sequential mode record_result is a harmless no-op."""
        mode = SequentialMode(sample_deck)
        card = mode.next_card()
        assert card is not None
        mode.record_result(card, False)
        next_card = mode.next_card()
        assert next_card is not None
        assert next_card.front == "What is git?"


class TestRandomMode:
    """Tests for random quiz mode."""

    def test_random_with_seeded_rng(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Random mode with seeded RNG gives reproducible order."""
        rng1 = random.Random(42)
        mode1 = RandomMode(sample_deck, rng=rng1)
        cards1 = []
        while True:
            card = mode1.next_card()
            if card is None:
                break
            cards1.append(card.front)

        rng2 = random.Random(42)
        mode2 = RandomMode(sample_deck, rng=rng2)
        cards2 = []
        while True:
            card = mode2.next_card()
            if card is None:
                break
            cards2.append(card.front)

        assert cards1 == cards2

    def test_random_permutation(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Random mode returns all cards, once each."""
        mode = RandomMode(sample_deck, rng=random.Random(42))
        cards = []
        while True:
            card = mode.next_card()
            if card is None:
                break
            cards.append(card)

        assert len(cards) == 3
        fronts = [card.front for card in cards]
        assert sorted(fronts) == sorted([c.front for c in sample_deck])

    def test_random_then_none(self, sample_deck: Sequence[Flashcard]) -> None:
        """Random mode returns None after all cards."""
        mode = RandomMode(sample_deck, rng=random.Random(42))
        for _ in range(3):
            mode.next_card()
        assert mode.next_card() is None

    def test_does_not_mutate_input_deck(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Random mode does not mutate the input deck."""
        deck_list = list(sample_deck)
        mode = RandomMode(sample_deck, rng=random.Random(42))
        mode.next_card()
        assert list(sample_deck) == deck_list

    def test_empty_deck_raises_error(self) -> None:
        """Empty deck raises ValueError."""
        with pytest.raises(ValueError):
            RandomMode([], rng=random.Random())

    def test_record_result_is_noop(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Random mode record_result is a harmless no-op."""
        mode = RandomMode(sample_deck, rng=random.Random(42))
        card = mode.next_card()
        assert card is not None
        mode.record_result(card, False)


class TestAdaptiveMode:
    """Tests for adaptive quiz mode with retry logic."""

    def test_adaptive_starts_in_order(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Adaptive mode starts with cards in file order."""
        mode = AdaptiveMode(sample_deck)
        cards = []
        for _ in range(3):
            card = mode.next_card()
            if card is not None:
                cards.append(card)
        fronts = [card.front for card in cards]
        assert fronts == [
            "What is Python?",
            "What is git?",
            "What is Linux?",
        ]

    def test_adaptive_mode_behavior(
        self, four_card_deck: Sequence[Flashcard]
    ) -> None:
        """Adaptive mode re-asks wrong cards after RETRY_GAP others."""
        mode = AdaptiveMode(four_card_deck)
        cards_in_order = []

        card_a = mode.next_card()
        assert card_a is not None and card_a.front == "Card A"
        cards_in_order.append(card_a.front)

        mode.record_result(card_a, False)

        card_b = mode.next_card()
        assert card_b is not None and card_b.front == "Card B"
        cards_in_order.append(card_b.front)

        card_c = mode.next_card()
        assert card_c is not None and card_c.front == "Card C"
        cards_in_order.append(card_c.front)

        card_a_retry = mode.next_card()
        assert card_a_retry is not None and card_a_retry.front == "Card A"
        cards_in_order.append(card_a_retry.front)

        assert cards_in_order == ["Card A", "Card B", "Card C", "Card A"]

    def test_correct_cards_not_repeated(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Correct cards are never repeated in adaptive mode."""
        mode = AdaptiveMode(sample_deck)
        seen_fronts = []

        while True:
            card = mode.next_card()
            if card is None:
                break
            if card.front not in seen_fronts:
                mode.record_result(card, True)
                seen_fronts.append(card.front)
            else:
                pytest.fail(
                    f"Card {card.front} was repeated after correct answer"
                )

    def test_adaptive_max_retries_enforced(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Adaptive mode stops re-asking after MAX_RETRIES."""
        mode = AdaptiveMode(sample_deck)
        card = mode.next_card()
        assert card is not None

        for _ in range(MAX_RETRIES + 2):
            mode.record_result(card, False)

        all_cards = []
        while True:
            c = mode.next_card()
            if c is None:
                break
            all_cards.append(c.front)

        count = sum(1 for front in all_cards if front == card.front)
        assert count <= MAX_RETRIES

    def test_adaptive_no_infinite_loop(
        self, four_card_deck: Sequence[Flashcard]
    ) -> None:
        """Adaptive mode terminates even with many wrong answers."""
        mode = AdaptiveMode(four_card_deck)
        cards_seen = 0

        for _ in range(100):
            card = mode.next_card()
            if card is None:
                break
            mode.record_result(card, False)
            cards_seen += 1

        assert cards_seen < 100

    def test_adaptive_respects_retry_gap(
        self, four_card_deck: Sequence[Flashcard]
    ) -> None:
        """Adaptive mode respects RETRY_GAP when asking retries."""
        mode = AdaptiveMode(four_card_deck)

        card_a = mode.next_card()
        assert card_a is not None and card_a.front == "Card A"
        mode.record_result(card_a, False)

        cards_between = []
        for _ in range(RETRY_GAP):
            card = mode.next_card()
            assert card is not None
            if card.front != "Card A":
                cards_between.append(card.front)

        next_card = mode.next_card()
        assert next_card is not None
        assert next_card.front == "Card A"

    def test_empty_deck_raises_error(self) -> None:
        """Empty deck raises ValueError."""
        with pytest.raises(ValueError):
            AdaptiveMode([])

    def test_adaptive_exact_sequence_one_miss(
        self, four_card_deck: Sequence[Flashcard]
    ) -> None:
        """Verify exact sequence: A wrong, rest right → A,B,C,A,D."""
        mode = AdaptiveMode(four_card_deck)
        sequence = []

        for _ in range(5):
            card = mode.next_card()
            if card is None:
                break
            sequence.append(card.front)
            if card.front == "Card A":
                mode.record_result(card, False)
            else:
                mode.record_result(card, True)

        assert sequence == ["Card A", "Card B", "Card C", "Card A", "Card D"]

    def test_adaptive_exact_sequence_all_wrong(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Every card wrong: each appears at most 1 + MAX_RETRIES times."""
        mode = AdaptiveMode(sample_deck)
        sequence = []

        for _ in range(100):
            card = mode.next_card()
            if card is None:
                break
            sequence.append(card.front)
            mode.record_result(card, False)

        for front in ["What is Python?", "What is git?", "What is Linux?"]:
            count = sum(1 for c in sequence if c == front)
            assert count <= 1 + MAX_RETRIES


class TestSessionStats:
    """Tests for session statistics tracking."""

    def test_stats_initialization(self) -> None:
        """SessionStats initializes with zero values."""
        stats = SessionStats()
        assert stats.total_questions == 0
        assert stats.correct == 0
        assert stats.missed_terms == []
        assert stats.accuracy_percent == 0.0

    def test_accuracy_percent_zero_questions(self) -> None:
        """Accuracy is 0.0 when no questions answered."""
        stats = SessionStats()
        assert stats.accuracy_percent == 0.0

    def test_accuracy_percent_calculation(self) -> None:
        """Accuracy percent is correctly calculated and rounded."""
        stats = SessionStats(total_questions=10, correct=7)
        assert stats.accuracy_percent == 70.0

        stats = SessionStats(total_questions=3, correct=1)
        assert stats.accuracy_percent == round(100.0 / 3, 1)

    def test_accuracy_percent_one_decimal(self) -> None:
        """Accuracy is rounded to one decimal place."""
        stats = SessionStats(total_questions=3, correct=1)
        accuracy = stats.accuracy_percent
        assert accuracy == 33.3
        assert isinstance(accuracy, float)


class TestQuizSession:
    """Tests for quiz session management."""

    def test_session_next_card_delegates_to_mode(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session next_card delegates to the mode."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None
        assert card.front == "What is Python?"

    def test_session_submit_correct_answer(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session correctly identifies correct answers."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None

        is_correct = session.submit_answer(card, "A programming language")
        assert is_correct is True
        assert session.stats.correct == 1
        assert session.stats.total_questions == 1

    def test_session_submit_incorrect_answer(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session correctly identifies incorrect answers."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None

        is_correct = session.submit_answer(card, "Wrong answer")
        assert is_correct is False
        assert session.stats.correct == 0
        assert session.stats.total_questions == 1

    def test_session_answer_case_insensitive(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session answers are case-insensitive."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None

        is_correct = session.submit_answer(card, "A PROGRAMMING LANGUAGE")
        assert is_correct is True

    def test_session_answer_whitespace_trimmed(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session answers have whitespace trimmed."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None

        is_correct = session.submit_answer(card, "  A programming language  ")
        assert is_correct is True

    def test_session_missed_terms_ordered(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Missed terms are unique and in first-missed order."""
        mode = AdaptiveMode(sample_deck)
        session = QuizSession(mode)

        cards_sequence = []
        for _ in range(4):
            card = session.next_card()
            if card is None:
                break
            cards_sequence.append(card.front)
            if card.front == "What is Python?":
                session.submit_answer(card, "wrong answer")
            elif card.front == "What is git?":
                session.submit_answer(card, "wrong answer")
            else:
                session.submit_answer(card, card.back)

        missed = session.stats.missed_terms
        assert missed == ["What is Python?", "What is git?"]
        assert cards_sequence == [
            "What is Python?",
            "What is git?",
            "What is Linux?",
            "What is Python?",
        ]

    def test_session_mixed_answers(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session correctly tracks mixed correct/incorrect answers."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)

        card1 = session.next_card()
        assert card1 is not None
        session.submit_answer(card1, "A programming language")

        card2 = session.next_card()
        assert card2 is not None
        session.submit_answer(card2, "wrong")

        card3 = session.next_card()
        assert card3 is not None
        session.submit_answer(card3, "An operating system")

        assert session.stats.total_questions == 3
        assert session.stats.correct == 2
        assert session.stats.accuracy_percent == round(200.0 / 3, 1)
        assert session.stats.missed_terms == ["What is git?"]

    def test_session_stats_property(
        self, sample_deck: Sequence[Flashcard]
    ) -> None:
        """Session stats property returns the same stats object."""
        mode = SequentialMode(sample_deck)
        session = QuizSession(mode)
        card = session.next_card()
        assert card is not None
        session.submit_answer(card, "A programming language")

        stats = session.stats
        assert stats.correct == 1
        assert stats.total_questions == 1
