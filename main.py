"""Entry point for the Flashcard Quizzer CLI application."""

import argparse
import os
import sys

from data_loader import DeckError, load_deck
from quiz_engine import QuizModeFactory, QuizSession
from ui import QuizUI, run_quiz


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        ArgumentParser configured for the flashcard quiz application.
    """
    parser = argparse.ArgumentParser(
        description="A terminal flashcard quiz application",
        epilog=(
            "Examples:\n"
            "  python main.py -f data/glossary.json\n"
            "  python main.py -f data/python_basics.json -m adaptive --stats"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-f",
        "--file",
        required=True,
        type=str,
        help="Path to the JSON flashcard deck",
    )

    parser.add_argument(
        "-m",
        "--mode",
        default="sequential",
        choices=QuizModeFactory.available_modes(),
        help="Quiz mode (default: sequential)",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show per-card statistics",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the flashcard quiz application.

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        deck = load_deck(args.file)
    except DeckError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    use_color = (
        sys.stdout.isatty()
        and os.environ.get("NO_COLOR") is None
        and not args.no_color
    )

    mode = QuizModeFactory.create(args.mode, deck)
    session = QuizSession(mode)
    ui = QuizUI(use_color=use_color)

    run_quiz(session, ui, show_details=args.stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
