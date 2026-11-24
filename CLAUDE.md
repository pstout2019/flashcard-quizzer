# Flashcard Quizzer: Project Rules

You are the builder; I am the architect and reviewer. Follow these rules on every task.
These rules add to `.claude/CLAUDE.md` (the course's file). Where they are more specific, these win.

## Project
A terminal flashcard quiz for new hires learning server acronyms. Python 3.10+, Linux, `pip` only (no Poetry/Pipenv, no virtual environment in this workspace). Install packages with `python -m pip install -r requirements.txt` and run every tool as `python -m <tool>`.

## Architecture (do not collapse into one file; do not delete starter folders)
- `main.py`: entry point only. Parses args, wires modules, catches errors, sets exit codes.
- `data_loader.py`: loads and validates decks into `Flashcard` objects.
- `utils/file_handler.py`: reads files from disk; raises clear errors for missing/unreadable files.
- `quiz_engine.py`: the `QuizMode` ABC, `SequentialMode`, `RandomMode`, `AdaptiveMode`, the mode factory, the quiz session and its stats.
- `ui.py`: all terminal input/output and colours. No quiz logic here.
- `data/`: JSON decks. `tests/`: pytest suite. `docs/`: log and report.

Dependencies flow one way: `main` → `ui` / `quiz_engine` / `data_loader` → `utils`. `quiz_engine` must not import `ui`.

## Design decisions (already made; do not change without asking)
- `Flashcard` is a frozen dataclass with `front: str` and `back: str`.
- Decks come in two formats: array `[{"front": ..., "back": ...}]` and object `{"cards": [...]}`. Anything else is invalid.
- **Strategy pattern**: `QuizMode` (ABC) defines the card-selection interface. Every mode implements the same methods, including a way to be told whether the last answer was correct (Sequential and Random ignore it; Adaptive uses it).
- **Factory**: one function or class in `quiz_engine.py` maps a mode name (`sequential`, `random`, `adaptive`) to a `QuizMode` instance and raises a clear error for unknown names.
- **Adaptive rule**: a missed card is re-queued to come back after RETRY_GAP (2) other cards, or sooner if fewer remain. Each card is re-asked at most MAX_RETRIES (3) times, so the session always ends. Correct cards are not repeated.
- Answers are correct when `answer.strip().casefold() == card.back.strip().casefold()`.
- `exit` (any case) or Ctrl+C / Ctrl+D ends the quiz cleanly and still shows the summary of questions answered so far.

## Code rules
- Type hints on **every** function and method, including tests (`-> None`). Code must pass `mypy`.
- Runtime code uses the **standard library only** (`argparse`, `json`, `random`, `dataclasses`, `abc`, `pathlib`, `sys`). Colours use ANSI escape codes. Ask before adding any runtime dependency.
- Never import a module or call an API you have not confirmed exists. If unsure, check it.
- Errors: the data layer raises custom exceptions (e.g. `DeckLoadError`, `DeckValidationError`) with messages naming the file and the problem (e.g. "card 3 is missing 'back'"). `main.py` catches them, prints a friendly message to stderr and exits with code 1. Users never see a traceback.
- Keep `ui.py` testable: pass input and output functions in (defaulting to `input` / `print`) rather than calling them directly from logic.
- No magic numbers or strings scattered in code; use named constants.
- Short functions. Google-style docstrings (Args / Returns / Raises) on public functions and classes that explain why and when, not just restate names.
- Prefer the simplest design that meets the requirements; no speculative abstractions.
- Treat deck files as untrusted input: parse only with `json` (never `eval`/`pickle`), validate every field, and keep error messages free of stack traces.
- Format with `black` and lint with `flake8`, both at **79** characters, set in config files only (`pyproject.toml` `[tool.black] line-length = 79`; `setup.cfg` `[flake8] max-line-length = 79`, `extend-ignore = E203, W503`). Never pass line-length flags on the command line; if tools disagree, fix the config.

## Tests
- `pytest`, in `tests/`. Arrange-Act-Assert, descriptive names, fixtures for sample decks, `tmp_path` for files, `monkeypatch` or injected functions for input. Never block on real stdin.
- Test behaviour, not implementation. No weak assertions like `assert result is not None`. Cover error paths and edge cases (empty deck, whitespace and case in answers, unknown mode).
- These tests must exist with these exact names:
  - `tests/test_flashcard_loader.py`: `test_load_valid_flashcards_array`, `test_load_invalid_json`, `test_load_missing_required_field`
  - `tests/test_quiz_modes.py`: `test_quiz_mode_factory`, `test_adaptive_mode_behavior`
  - `tests/test_integration.py`: `test_full_session`
- Coverage target above 80% with `python -m pytest --cov=. --cov-report=html`; `.coveragerc` omits `tests/*`, `venv/*`, `.venv/*`.

## Definition of done (run from the starter folder before saying a task is finished)
1. `python -m isort .` (configured with `profile = "black"`, `line_length = 79` in `pyproject.toml`)
2. `python -m black .`
3. `python -m flake8 .` → zero errors
4. `python -m mypy .` → no errors
5. `python -m pytest tests/ --cov=. --cov-report=term-missing` → all pass

Show the result of every step in your report. Plain commands only, no extra flags.

If any step fails, fix it and re-run. Never report a task as done with failing checks; if you can't fix something, say so plainly.

## How to work with me (we have a token budget)
- Do one phase or task per request. Don't start the next phase unprompted.
- Ask before guessing when a requirement is ambiguous.
- If my requirement contradicts correct behaviour or the spec, say so and ask. Don't change working code to fit it.
- Never delete, skip or weaken a test or a check to make it pass. If you can't fix it, stop and report.
- Don't echo whole files back. End each task with a short report:
  - files created or changed
  - design decisions and assumptions you made
  - results of the four checks (pass/fail counts, coverage %)
  - anything you're unsure about or that I should review
- Before reporting, review your own code for: invented imports, missing error handling, untested branches, hard-coded values, and logic that doesn't match these rules. List what you found and fixed.
- Don't edit `docs/ai_edit_log.md` or `docs/report_template.md` unless I ask; I write those.
- Don't commit or push unless I ask. When I ask, use one clear commit message per phase.
- `ai_guidance/` holds the course's review checklist and prompting guide. Read it only when I ask for a review.

