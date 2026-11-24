"""Module for loading and validating flashcard decks from JSON files."""

import json
from dataclasses import dataclass
from pathlib import Path

from utils.file_handler import FileHandlerError, read_text_file

MAX_DECK_SIZE = 1_000_000  # 1 MB


class DeckError(Exception):
    """Base exception for deck loading and validation errors."""

    pass


class DeckLoadError(DeckError):
    """Exception raised when a deck file cannot be read or parsed."""

    pass


class DeckValidationError(DeckError):
    """Exception raised when a deck file structure is invalid."""

    pass


@dataclass(frozen=True)
class Flashcard:
    """A single flashcard with a question (front) and answer (back).

    Attributes:
        front: The question or prompt text.
        back: The answer or response text.
    """

    front: str
    back: str


def load_deck(path: str | Path) -> list[Flashcard]:
    """Load and validate a flashcard deck from a JSON file.

    Accepts either a top-level array of cards or a top-level object with a
    "cards" key containing an array. Each card must be an object with
    non-empty "front" and "back" string fields (after stripping whitespace).
    Extra keys on cards are ignored.

    Args:
        path: Path to the JSON file containing the deck.

    Returns:
        A list of Flashcard objects in the order they appear in the file.

    Raises:
        DeckLoadError: If the file cannot be read, is too large, or contains
            invalid JSON.
        DeckValidationError: If the deck structure is invalid or empty.
    """
    path_obj = Path(path)
    file_path_str = str(path_obj)

    try:
        file_size = path_obj.stat().st_size
        if file_size > MAX_DECK_SIZE:
            raise DeckLoadError(
                f"Deck file is too large ({file_size} bytes, "
                f"max {MAX_DECK_SIZE}): {file_path_str}"
            )
    except FileNotFoundError as e:
        raise DeckLoadError(f"File not found: {file_path_str}") from e

    try:
        content = read_text_file(path_obj)
    except FileHandlerError as e:
        raise DeckLoadError(str(e)) from e

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise DeckLoadError(
            f"Invalid JSON in {file_path_str} at line {e.lineno}, "
            f"column {e.colno}: {e.msg}"
        ) from e

    cards_list: list[dict] = []
    if isinstance(data, list):
        cards_list = data
    elif isinstance(data, dict):
        if "cards" not in data:
            raise DeckValidationError(
                f"Deck file {file_path_str} is missing 'cards' key"
            )
        cards_list = data["cards"]
        if not isinstance(cards_list, list):
            raise DeckValidationError(
                f"'cards' field in {file_path_str} is not a list"
            )
    else:
        raise DeckValidationError(
            f"Deck file {file_path_str} must be a list or object, "
            f"not {type(data).__name__}"
        )

    if not cards_list:
        raise DeckValidationError(f"Deck file {file_path_str} is empty")

    flashcards = []
    for card_num, card in enumerate(cards_list, start=1):
        if not isinstance(card, dict):
            raise DeckValidationError(
                f"card {card_num} in {file_path_str} is not an object"
            )

        front = card.get("front")
        if not isinstance(front, str) or not front.strip():
            raise DeckValidationError(
                f"card {card_num} in {file_path_str}: "
                f"'front' must be a non-empty string"
            )

        back = card.get("back")
        if not isinstance(back, str) or not back.strip():
            raise DeckValidationError(
                f"card {card_num} in {file_path_str}: "
                f"'back' must be a non-empty string"
            )

        flashcards.append(Flashcard(front=front.strip(), back=back.strip()))

    return flashcards
