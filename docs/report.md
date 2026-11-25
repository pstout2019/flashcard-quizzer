# AI-Assisted Development Project Report

**Student Name:** Phil Stout
**Project Title:** Flashcard Quizzer CLI
**Date:** 2026-11-24

## Executive Summary

I built the Flashcard Quizzer, a terminal application that helps new hires memorise server acronyms and other terms. It loads decks from JSON in two formats, quizzes in sequential, random or adaptive mode, gives colour-coded feedback, and ends with an accuracy summary.

I worked as architect and reviewer; Claude Code in the lab workspace wrote all 2,434 lines of Python. I wrote structured XML prompts, set standing rules in a project CLAUDE.md, reviewed every diff and report, and sent correction prompts rather than hand-editing code. A second AI assistant helped me draft prompts and review the agent's output.

The main finding: the agent was strong at implementing a clear specification but repeatedly made failing checks pass by weakening them, then overstated what it had verified. Most of my value was in catching that.

## Project Overview

### Problem Statement
New hires need a lightweight way to learn internal terminology in the terminal, and the code must be easy to extend, for example with spaced repetition.

### Solution Approach
- **Architecture:** five modules with one-way dependencies: `main.py`, then `ui.py` and `quiz_engine.py`, then `data_loader.py`, then `utils/file_handler.py`. `quiz_engine.py` never imports the UI.
- **Key decisions made before prompting:** an Adaptive rule (a missed card returns after 2 other cards, at most 3 retries, so sessions always end); a `record_result()` hook on every mode so Adaptive can learn without breaking the Strategy interface; an injected random-number generator so shuffling is testable; deck files treated as untrusted input (JSON only, field validation, 1 MB limit).
- **Stack:** Python 3.10 standard library only; pytest, pytest-cov, black, isort, flake8 and mypy for quality.

### Final Features
- [x] Load and validate array and object decks, with friendly one-line errors (exit code 1)
- [x] Quiz loop with case- and whitespace-insensitive answers and green/red feedback
- [x] Sequential, Random and Adaptive modes (Strategy) selected by `QuizModeFactory`
- [x] Summary: Total Questions, Accuracy %, missed terms
- [x] `--stats` per-card breakdown; `--no-color`; `exit`, Ctrl+C and Ctrl+D quit cleanly with a summary
- [x] A new `server_acronyms.json` deck

## AI Collaboration Experience

### AI Tools Used
- [x] Claude: Claude Code in the lab workspace (Claude Haiku 4.5), the builder
- [x] Other: a second Claude assistant outside the lab, for drafting prompts and reviewing output

### Collaboration Workflow
1. **Prompts:** one phase per prompt, in XML with `<task>`, `<context>`, `<requirements>`, `<tests>`, `<constraints>` and `<output>`, including exact test names and expected values.
2. **Tasks:** code, tests, configuration, the README and a final requirements audit.
3. **Review:** I read diffs, not summaries, against the course's code review checklist, checked every claimed result against command output, and played the game myself.
4. **Refinement:** precise correction prompts, and standing rules added to CLAUDE.md whenever a failure pattern repeated.

### Most Valuable AI Interactions

#### Example 1: Quiz engine from one structured prompt
**Context:** Strategy and Factory for three modes. **AI Prompt:** the interface, the Adaptive rule, the injected rng and the registry requirement. **AI Response:** a clean design with 35 tests asserting exact card sequences. **Your Changes:** the factory had been turned into if/elif to silence mypy; I had the typed registry restored, unified the constructors, and matched the course's factory-class style. **Outcome:** extensible with one class plus one registry entry; 100% coverage.

#### Example 2: Data layer with defensive validation
**Context:** two JSON formats with friendly errors. **AI Prompt:** exact exceptions, messages and a size limit checked before parsing. **AI Response:** correct standard-library code. **Your Changes:** rewrote the tests for the required names, matching messages, type hints and missing edge cases. **Outcome:** 36 tests, 100% coverage.

#### Example 3: Root-causing the untestable CLI
**Context:** end-to-end `main()` tests failed. **AI Prompt:** restore the tests and fix the cause. **AI Response:** once directed, it changed `QuizUI` to look up `input` and `print` when created. **Your Changes:** required output assertions, not just exit codes. **Outcome:** `main.py` at 100% coverage, with graceful exits proven.

### Challenges with AI Collaboration
The agent struggled most with honesty under pressure. It declared "complete" without running the checks; worked around a config conflict with command-line flags; reported a registry it had removed; weakened one test and deleted five; relaxed mypy for the tests; and wrote a README with invented `--help` output and non-existent methods. It also complied with my own incorrect requirement by changing working code. Its strengths were speed, consistent structure and thorough test permutations when expectations were explicit.

## Software Engineering Practices

### Code Quality Measures
- [x] Code formatting (black, isort), configured in files only, at 79 characters
- [x] Linting (flake8: zero errors; mypy with `disallow_untyped_defs = True`)
- [x] Type hints on every function, including tests
- [x] Google-style docstrings; README verified against real output
- [x] Error handling with a custom exception hierarchy; no bare `except`

### Testing Strategy
104 unit and integration tests at 100% coverage. They assert exact sequences and messages rather than "not None"; use `tmp_path`, `monkeypatch` and `capsys`; and cover error paths (invalid UTF-8, permissions, oversized files). This was spec-first rather than strict TDD: each prompt defined the tests and expected values alongside the code.

### Design Patterns Used
- **Strategy:** `QuizMode` (ABC) with `SequentialMode`, `RandomMode` and `AdaptiveMode`; `QuizSession` is the context and never checks the concrete type.
- **Factory:** `QuizModeFactory` with a typed registry feeding creation, `--mode` choices and error messages.

### Code Structure and Organization
Data, logic and presentation are separated as described above. Refactoring: the factory class, unified constructors, and injectable UI input and output.

## Technical Challenges and Solutions

### Challenge 1: Tool configuration conflicts
**Problem:** flake8 used 79 characters, black 88, coverage counted the tests, and a `pyproject.toml` setting quietly disabled mypy's type-hint check. **Solution:** found the config files had never been created; consolidated the settings into `setup.cfg`, `pyproject.toml` and `.coveragerc`, with no command-line flags. **AI Involvement:** the agent implemented the fix once I found the root cause. **Lessons Learned:** fix configuration, not commands.

### Challenge 2: `input` bound at import time
**Problem:** monkeypatching `builtins.input` had no effect. **Solution:** resolve `input` and `print` in `QuizUI.__init__`, not in default arguments. **AI Involvement:** the agent had deleted the tests instead of diagnosing this; after redirection it implemented the fix. **Lessons Learned:** default arguments are evaluated once, when the function is defined.

### Challenge 3: Instructions not loaded
**Problem:** early sessions ignored my rules. **Solution:** the file was `claude.md` in the parent folder; Linux is case-sensitive. Moved it and confirmed with `/memory`. **Lessons Learned:** verify the agent has its instructions.

## Code Quality Analysis

### Metrics
- Lines of code: 2,434 Python (application and tests)
- Test coverage: 100% (104 tests)
- Number of functions/classes: 14 classes; 27 functions and methods in the application code (tests excluded)
- Linting score: flake8 0 errors; black, isort and mypy pass

### Self-Assessment
- **Code Readability:** 4. Consistent formatting, descriptive names, docstrings; some test files are long.
- **Code Maintainability:** 5. Strict module boundaries; a new mode is one class plus one registry entry.
- **Test Quality:** 4. Behavioural, exact assertions at 100% coverage, but reaching that needed several corrections.
- **Documentation:** 4. The README is verified against the code; it needed two correction rounds.

## Learning Outcomes

### Technical Skills Developed
Strategy and Factory in Python, pytest fixtures (`monkeypatch`, `capsys`), and configuring the tools so they agree.

### AI Collaboration Skills
Structured XML prompts with exact expectations; standing rules in CLAUDE.md; reading diffs over summaries; and treating every claim of "done" as unverified until checked.

### Software Engineering Insights
A test proves only what it asserts; documentation needs the same verification as code; and specifications can be wrong, so the agent should be asked to challenge them.

## Reflection

### What Worked Well
Making design decisions before prompting, one phase per prompt, and turning each failure into a permanent rule. After the "never weaken tests" and "push back on wrong requirements" rules were added, the agent honoured both.

### What Could Be Improved
I'd verify the rules file loads first, require a diff summary in every report, and pin tool configuration during setup.

### Future Enhancements
Spaced repetition with saved progress, multiple accepted answers per card, and a summary table that fits long questions.

## Conclusion
AI-assisted development moved my role from writing code to specifying and verifying it. Coming from Azure and infrastructure work, it felt like Terraform plan review: the agent proposes, I read the plan, and nothing is accepted until the diff matches the intent. Python test design was where I was rustiest, and this project rebuilt that habit. The skill that mattered most was refusing to accept a green check at face value. I'll keep using structured prompts, standing rules and diff-first review.

## Appendices

### Appendix A: AI Interaction Log
See `docs/ai_edit_log.md`, especially the misreported factory, the weakened tests and the wrong requirement.

### Appendix B: Code Statistics
See `docs/coverage_report.txt` and `htmlcov/index.html`.

### Appendix C: Additional Resources
`ai_guidance/code_review_checklist.md`, `ai_guidance/prompting_best_practices.md`, `docs/design_patterns.md`.
