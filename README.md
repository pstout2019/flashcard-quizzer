# Flashcard Quizzer

A command-line tool that loads flashcards from JSON files and quizzes you in sequential, random, or adaptive mode.

## Overview

The Flashcard Quizzer helps you memorize concepts by displaying flashcards and tracking your performance. It supports three quiz modes:

- **Sequential Mode**: Cards appear in the order they appear in the deck.
- **Random Mode**: Cards appear in random order.
- **Adaptive Mode**: Cards appear strategically. When you miss a card, it re-enters the queue to appear again after RETRY_GAP (2) other cards. Each card is re-asked at most MAX_RETRIES (3) times, ensuring every session finishes.

## Requirements

- Python 3.10 or later
- No runtime dependencies (uses only the Python standard library)
- `requirements.txt` contains development and testing tools

## Installation

Install development and testing tools:

```bash
python -m pip install -r requirements.txt
```

Optionally, create a virtual environment on your own machine:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Quick Start

Run the quiz with the default sequential mode:

```bash
python main.py -f data/python_basics.json
```

Run with random mode:

```bash
python main.py -f data/python_basics.json -m random
```

Run with adaptive mode:

```bash
python main.py -f data/server_acronyms.json -m adaptive
```

Show per-card statistics after the quiz:

```bash
python main.py -f data/python_basics.json --stats
```

## Usage

### Help

View all available flags:

```bash
python main.py --help
```

Output:
```
usage: main.py [-h] -f FILE [-m {adaptive,random,sequential}] [--stats]
               [--no-color]

A terminal flashcard quiz application

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to the JSON flashcard deck
  -m {adaptive,random,sequential}, --mode {adaptive,random,sequential}
                        Quiz mode (default: sequential)
  --stats               Show per-card statistics
  --no-color            Disable colored output

Examples:
  python main.py -f data/glossary.json
  python main.py -f data/python_basics.json -m adaptive --stats
```

### Flags

#### `-f FILE`, `--file FILE`

Specify the path to a JSON flashcard deck. This flag is required.

Example:
```bash
python main.py -f data/glossary.json
```

#### `-m MODE`, `--mode MODE`

Choose the quiz mode: `sequential`, `random`, or `adaptive`. Default: `sequential`

Example:
```bash
python main.py -m adaptive -f data/server_acronyms.json
```

#### `--stats`

Include per-card statistics in the quiz summary showing attempts and correct answers for each card.

Example:
```bash
python main.py --stats -f data/python_basics.json
```

Output includes:
```
========================================
Quiz Summary
========================================
Total Questions: 2
Correct: 1
Accuracy %: 50.0
Missed Terms: Which built-in function returns the length of a list?

----------------------------------------
Per-Card Statistics
----------------------------------------
Card                           Attempts   Correct   
----------------------------------------
Which keyword defines a function? 1          1         
Which built-in function returns the length of a list? 1          0
```

#### `--no-color`

Disable ANSI color codes. Useful for terminals that don't support colors.

Example:
```bash
python main.py --no-color -f data/python_basics.json
```

## Deck Format

Flashcard decks are JSON files. Two formats are supported:

### Array Format

A simple list of card objects:

```json
[
  {
    "front": "What is Python?",
    "back": "A high-level programming language"
  },
  {
    "front": "What does REST stand for?",
    "back": "Representational State Transfer"
  }
]
```

### Object Format

A single object with a `cards` array:

```json
{
  "cards": [
    {
      "front": "What is Python?",
      "back": "A high-level programming language"
    },
    {
      "front": "What does REST stand for?",
      "back": "Representational State Transfer"
    }
  ]
}
```

### Validation Rules

- Deck must be a valid JSON array or object with a `cards` key.
- Deck must not be empty.
- Each card must be an object with `front` and `back` fields.
- Both `front` and `back` must be non-empty strings.
- Whitespace at the beginning and end of `front` and `back` is automatically stripped.
- File must not exceed 1 MB.

### Included Decks

- `data/glossary.json`: Glossary of technical terms
- `data/python_basics.json`: Python fundamentals
- `data/server_acronyms.json`: Common server and infrastructure acronyms

## During a Quiz

### Answering Questions

The quizzer displays a question and waits for your answer. Answers are:
- **Case-insensitive**: "DNS" and "dns" are both correct.
- **Whitespace-insensitive**: "  Domain Name System  " and "Domain Name System" are both correct.
- **Exact**: The answer must match the expected back of the card after case and whitespace normalization.

Blank answers (just pressing Enter) are ignored and re-prompt without counting as an attempt.

### Ending the Quiz

You can quit the quiz at any time:

- Type `exit` and press Enter
- Press Ctrl+C (KeyboardInterrupt)
- Press Ctrl+D (EOFError / EOF)

The quiz displays a summary of your progress before exiting.

## Exit Codes

- `0`: Quiz completed successfully, or quit gracefully with Ctrl+C/Ctrl+D/exit
- `1`: Error loading or validating the deck file
- `2`: Invalid arguments provided to the command

## Troubleshooting

### File Not Found

**Error:**
```
Error: File not found: data/my_deck.json
```

**Fix:** Check the file path. Use an absolute path or verify the file is in the current directory:
```bash
python main.py -f /full/path/to/deck.json
```

### Invalid JSON

**Error:**
```
Error: Invalid JSON in data/my_deck.json at line 1, column 3: Expecting property name enclosed in double quotes
```

**Fix:** Validate your JSON file. Check for missing commas, quotes, or braces. Use a JSON validator online or in your editor.

### Missing Required Field

**Error:**
```
Error: card 2 in data/my_deck.json: 'back' must be a non-empty string
```

**Fix:** Ensure every card has both `front` and `back` fields. Check the specific card number mentioned in the error.

### Unknown Mode

**Error:**
```
usage: main.py [-h] -f FILE [-m {adaptive,random,sequential}] [--stats]
               [--no-color]
main.py: error: argument -m/--mode: invalid choice: 'unknown' (choose from 'adaptive', 'random', 'sequential')
```

**Fix:** Use only `sequential`, `random`, or `adaptive`. Check your `-m` or `--mode` flag:
```bash
python main.py -m random -f data/glossary.json
```

## Design

### Module Responsibilities

- **`main.py`**: Entry point. Parses arguments, loads the deck, initializes the UI and engine, runs the quiz, catches errors, and sets exit codes.
- **`data_loader.py`**: Loads and validates flashcard decks from JSON files. Raises clear errors for missing/malformed/invalid files.
- **`quiz_engine.py`**: Implements the quiz session logic, card-selection strategies, session statistics, and mode factory.
- **`ui.py`**: Terminal input/output and color formatting. All user-facing output happens here.
- **`utils/file_handler.py`**: Low-level file reading with clear error messages for missing/unreadable files.

### Design Patterns

#### Strategy Pattern

The quizzer uses the Strategy pattern to implement different quiz modes. All modes implement the same interface:

- **`QuizMode` (ABC)**: Abstract base class defining the interface for card selection.
- **`SequentialMode`**: Returns cards in deck order.
- **`RandomMode`**: Returns cards in random order.
- **`AdaptiveMode`**: Returns cards strategically, re-queuing missed cards.

#### Factory Pattern

The `QuizModeFactory` class creates the appropriate mode instance:

```python
mode = QuizModeFactory.create("adaptive", deck)
```

Unknown mode names raise `UnknownModeError`.

### Adding a New Mode

To add a new quiz mode:

1. Create a new class inheriting from `QuizMode` in `quiz_engine.py`.
2. Implement the `next_card()` method.
3. Override `record_result(card: Flashcard, correct: bool) -> None` only if the mode reacts to answers.
4. Add one entry to `QuizModeFactory._REGISTRY`.

Example:

```python
class ShuffledMode(QuizMode):
    def __init__(self, cards: Sequence[Flashcard], rng: random.Random | None = None) -> None:
        super().__init__(cards, rng=rng)
        self._shuffled = list(cards)
        self._index = 0
    
    def next_card(self) -> Flashcard | None:
        if self._index >= len(self._shuffled):
            return None
        card = self._shuffled[self._index]
        self._index += 1
        return card
    
    def record_result(self, card: Flashcard, correct: bool) -> None:
        # Only override if your mode needs to react to answers
        pass

# In QuizModeFactory._REGISTRY:
_REGISTRY = {
    "sequential": SequentialMode,
    "random": RandomMode,
    "adaptive": AdaptiveMode,
    "shuffled": ShuffledMode,  # Add your new mode here
}
```

## Development

Run these quality checks before committing:

```bash
python -m isort .
python -m black .
python -m flake8 .
python -m mypy .
python -m pytest tests/ --cov=. --cov-report=term-missing
```

Expected results:
- **isort**: Silently organizes imports
- **black**: Silently formats code
- **flake8**: Prints nothing when clean (no errors or warnings)
- **mypy**: "Success: no issues found in X source files"
- **pytest**: All tests pass, coverage above 80%

Coverage report (HTML):

```bash
python -m pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the coverage report.
