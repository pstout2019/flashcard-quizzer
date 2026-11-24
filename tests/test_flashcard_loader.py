"""Tests for flashcard deck loading and validation."""

import json
from pathlib import Path

import pytest

from data_loader import (
    MAX_DECK_SIZE,
    DeckError,
    DeckLoadError,
    DeckValidationError,
    Flashcard,
    load_deck,
)


class TestLoadValidDecks:
    """Tests for successfully loading valid decks."""

    def test_load_valid_flashcards_array(self, tmp_path: Path) -> None:
        """Load a valid array-format deck."""
        deck_file = tmp_path / "deck.json"
        deck_data = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2", "back": "A2"},
            {"front": "Q3", "back": "A3"},
        ]
        deck_file.write_text(json.dumps(deck_data))

        result = load_deck(deck_file)

        assert len(result) == 3
        assert result[0] == Flashcard(front="Q1", back="A1")
        assert result[1] == Flashcard(front="Q2", back="A2")
        assert result[2] == Flashcard(front="Q3", back="A3")

    def test_load_valid_flashcards_object(self, tmp_path: Path) -> None:
        """Load a valid object-format deck with 'cards' key."""
        deck_file = tmp_path / "deck.json"
        deck_data = {
            "cards": [
                {"front": "What is 2+2?", "back": "4"},
                {"front": "What is the capital of France?", "back": "Paris"},
            ]
        }
        deck_file.write_text(json.dumps(deck_data))

        result = load_deck(deck_file)

        assert len(result) == 2
        assert result[0] == Flashcard(front="What is 2+2?", back="4")
        assert result[1] == Flashcard(
            front="What is the capital of France?", back="Paris"
        )

    def test_whitespace_stripped_from_cards(self, tmp_path: Path) -> None:
        """Whitespace is stripped from front and back."""
        deck_file = tmp_path / "deck.json"
        deck_data = [{"front": "  Q1  ", "back": "\n A1 \t"}]
        deck_file.write_text(json.dumps(deck_data))

        result = load_deck(deck_file)

        assert result[0] == Flashcard(front="Q1", back="A1")

    def test_extra_keys_on_card_ignored(self, tmp_path: Path) -> None:
        """Extra keys on card objects are ignored."""
        deck_file = tmp_path / "deck.json"
        deck_data = [
            {"front": "Q", "back": "A", "extra": "value", "another": 123}
        ]
        deck_file.write_text(json.dumps(deck_data))

        result = load_deck(deck_file)

        assert len(result) == 1
        assert result[0] == Flashcard(front="Q", back="A")

    def test_load_glossary_sample_deck(self) -> None:
        """Load the provided glossary.json sample without errors."""
        data_dir = Path(__file__).resolve().parent.parent / "data"
        deck = load_deck(data_dir / "glossary.json")

        assert len(deck) > 0
        assert all(isinstance(card, Flashcard) for card in deck)
        assert all(card.front for card in deck)
        assert all(card.back for card in deck)

    def test_load_python_basics_sample_deck(self) -> None:
        """Load the provided python_basics.json sample without errors."""
        data_dir = Path(__file__).resolve().parent.parent / "data"
        deck = load_deck(data_dir / "python_basics.json")

        assert len(deck) > 0
        assert all(isinstance(card, Flashcard) for card in deck)
        assert all(card.front for card in deck)
        assert all(card.back for card in deck)

    def test_load_server_acronyms_deck(self) -> None:
        """Load server_acronyms.json with 15 cards and no duplicate fronts."""
        data_dir = Path(__file__).resolve().parent.parent / "data"
        deck = load_deck(data_dir / "server_acronyms.json")

        assert len(deck) == 15
        assert all(isinstance(card, Flashcard) for card in deck)
        fronts = [card.front for card in deck]
        assert len(fronts) == len(set(fronts))


class TestMissingRequiredFields:
    """Tests for cards with missing or empty required fields."""

    def test_load_missing_required_field(self, tmp_path: Path) -> None:
        """Card without 'back' field raises DeckValidationError with number."""
        deck_file = tmp_path / "deck.json"
        deck_data = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2"},  # missing back
        ]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 2" in error_msg
        assert "'back'" in error_msg

    def test_missing_front_field(self, tmp_path: Path) -> None:
        """Missing 'front' field raises DeckValidationError with number."""
        deck_file = tmp_path / "deck.json"
        deck_data = [{"back": "A1"}]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 1" in error_msg
        assert "'front'" in error_msg

    def test_card_back_is_number(self, tmp_path: Path) -> None:
        """Card with numeric 'back' raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data = [{"front": "Q1", "back": 42}]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 1" in error_msg
        assert "'back' must be a non-empty string" in error_msg

    def test_card_with_empty_front(self, tmp_path: Path) -> None:
        """Card with empty string front raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data = [{"front": "", "back": "A1"}]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 1" in error_msg
        assert "'front' must be a non-empty string" in error_msg

    def test_card_with_whitespace_only_back(self, tmp_path: Path) -> None:
        """Card with whitespace-only back raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data = [{"front": "Q1", "back": "   \t\n  "}]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 1" in error_msg
        assert "'back' must be a non-empty string" in error_msg


class TestInvalidStructure:
    """Tests for invalid deck structures."""

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON raises DeckLoadError with file, line and column."""
        deck_file = tmp_path / "deck.json"
        deck_file.write_text("[{invalid json}]")

        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "deck.json" in error_msg
        assert "Invalid JSON" in error_msg
        assert "line" in error_msg.lower()
        assert "column" in error_msg.lower()

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Missing file raises DeckLoadError."""
        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(tmp_path / "nonexistent.json")

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "not found" in error_msg

    def test_file_over_size_limit_rejected(self, tmp_path: Path) -> None:
        """File larger than 1 MB is rejected before parsing."""
        deck_file = tmp_path / "large.json"
        # Create a file larger than MAX_DECK_SIZE with valid JSON structure
        large_data = [{"front": "Q", "back": "A" * (MAX_DECK_SIZE + 1)}]
        deck_file.write_text(json.dumps(large_data))

        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "too large" in error_msg.lower()
        assert str(MAX_DECK_SIZE) in error_msg

    def test_file_over_size_limit_with_invalid_json(
        self, tmp_path: Path
    ) -> None:
        """File over size limit reports 'too large', not parse error."""
        deck_file = tmp_path / "toolarge.json"
        # Write a file that is definitely too large and has invalid JSON
        # We write padding plus invalid JSON to exceed the limit
        content = "[" * (MAX_DECK_SIZE + 1000)
        deck_file.write_text(content)

        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        # Should report size issue, not JSON parse error
        assert "too large" in error_msg.lower()

    def test_top_level_string_rejected(self, tmp_path: Path) -> None:
        """Top-level string raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_file.write_text('"just a string"')

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "must be a list or object" in str(exc_info.value)

    def test_top_level_number_rejected(self, tmp_path: Path) -> None:
        """Top-level number raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_file.write_text("42")

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "must be a list or object" in str(exc_info.value)

    def test_object_without_cards_key_rejected(self, tmp_path: Path) -> None:
        """Object without 'cards' key raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data = {"data": [{"front": "Q", "back": "A"}]}
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "cards" in str(exc_info.value).lower()

    def test_cards_field_not_a_list_rejected(self, tmp_path: Path) -> None:
        """'cards' field that isn't a list raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data = {"cards": "not a list"}
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "not a list" in str(exc_info.value)

    def test_card_that_is_not_object_rejected(self, tmp_path: Path) -> None:
        """Card that isn't an object raises DeckValidationError with number."""
        deck_file = tmp_path / "deck.json"
        deck_data = [
            {"front": "Q1", "back": "A1"},
            "just a string",  # not an object
        ]
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "card 2" in error_msg
        assert "not an object" in error_msg

    def test_directory_path_raises_error(self, tmp_path: Path) -> None:
        """Passing a directory path raises DeckLoadError."""
        with pytest.raises(DeckLoadError):
            load_deck(tmp_path)

    def test_invalid_utf8_file_raises_error(self, tmp_path: Path) -> None:
        """File with invalid UTF-8 bytes raises DeckLoadError."""
        deck_file = tmp_path / "bad.json"
        # Write invalid UTF-8 bytes directly
        deck_file.write_bytes(b"\x80\x81\x82")

        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(deck_file)

        error_msg = str(exc_info.value)
        assert "UTF-8" in error_msg or "utf-8" in error_msg.lower()


class TestEmptyDecks:
    """Tests for empty or invalid decks."""

    def test_empty_array_raises_error(self, tmp_path: Path) -> None:
        """Empty array raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_file.write_text("[]")

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "empty" in str(exc_info.value).lower()

    def test_empty_cards_list_raises_error(self, tmp_path: Path) -> None:
        """Object with empty 'cards' list raises DeckValidationError."""
        deck_file = tmp_path / "deck.json"
        deck_data: dict = {"cards": []}
        deck_file.write_text(json.dumps(deck_data))

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "empty" in str(exc_info.value).lower()


class TestErrorHandling:
    """Tests for error types and exception handling"""

    def test_both_error_types_caught_as_deck_error(
        self, tmp_path: Path
    ) -> None:
        """Both error types can be caught as DeckError."""
        # Test DeckLoadError
        load_error_file = tmp_path / "load.json"
        load_error_file.write_text("[")

        with pytest.raises(DeckError):
            load_deck(load_error_file)

        # Test DeckValidationError
        validation_error_file = tmp_path / "validation.json"
        validation_error_file.write_text("[]")

        with pytest.raises(DeckError):
            load_deck(validation_error_file)

    def test_load_error_includes_filename(self, tmp_path: Path) -> None:
        """DeckLoadError message includes the filename."""
        deck_file = tmp_path / "my_deck.json"
        deck_file.write_text("[")  # invalid JSON

        with pytest.raises(DeckLoadError) as exc_info:
            load_deck(deck_file)

        assert "my_deck.json" in str(exc_info.value)

    def test_validation_error_includes_filename(self, tmp_path: Path) -> None:
        """DeckValidationError message includes the filename."""
        deck_file = tmp_path / "bad_deck.json"
        deck_file.write_text("[]")  # empty

        with pytest.raises(DeckValidationError) as exc_info:
            load_deck(deck_file)

        assert "bad_deck.json" in str(exc_info.value)
