# AI Edit Log

**Project:** Flashcard Quizzer CLI
**Builder:** Claude Code in the Udacity lab workspace (Claude Haiku 4.5)
**Process note:** I drafted structured prompts and reviewed the lab agent's output with the help of a second AI assistant. Every prompt sent, every correction and every acceptance decision was mine. Code changes were made by directing the agent with correction prompts, not by hand-editing Python.

---

## Your Log Entries

### 2026-11-24 - Phase 1: Data loader tests didn't match the spec

**Context:** Phase 1 needed a loader for two JSON deck formats with friendly errors, plus `tests/test_flashcard_loader.py` containing three tests with exact required names.

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** A structured XML prompt (`<task>`, `<context>`, `<requirements>`, `<tests>`, `<constraints>`, `<output>`) specifying `utils/file_handler.py`, `data_loader.py` (a `Flashcard` dataclass, a `DeckError` hierarchy, `load_deck()`, a 1 MB size limit checked before parsing) and the test list. My pasted prompt accidentally dropped the line for `test_load_valid_flashcards_array`.

**AI Response:** The loader code was solid: standard library only, specific exceptions, `raise ... from`, and the size check via `stat()` before reading. The test file had problems: two required tests were renamed (`test_invalid_json_includes_line_and_column`, `test_card_missing_back_field`); five assertions checked lowercase `"card 2"` while the code produced `"Card 2"`; no type hints; sample-deck paths that only worked from one directory; and `issubclass` tests that checked structure, not behaviour.

**Changes Made:** I rejected the test file and sent a correction prompt with seven specific fixes:
- restore the exact required names
- lowercase the messages to match the spec, without weakening the assertions
- `tmp_path: Path` and `-> None` on every test
- paths built from `Path(__file__)`
- a test proving an oversized invalid-JSON file reports "too large" (so the size check runs first)
- tests for a directory, invalid UTF-8 and a numeric `back`
- one behavioural `DeckError` test replacing the three `issubclass` tests

I also made the `front` and `back` messages consistent ("'back' must be a non-empty string").

**Reasoning:** The rubric checks exact test names. Mismatched messages would have failed five tests, and the risk was that the agent would "fix" them by loosening the assertions. Tests that depend on the working directory are fragile in CI.

**Outcome:** 27 loader tests passing, `data_loader.py` at 100% coverage, and both sample decks verified to load.

**Lessons Learned:**
- Review the test file as carefully as the code; the code was right and the tests were wrong.
- The agent inferred one dropped requirement but silently renamed two others. Exact names must be stated exactly.
- Tell the agent *how* to fix a failing assertion, or it may weaken it.

---

### 2026-11-24 - "Phase 1 complete" without running the quality gate

**Context:** My project rules (CLAUDE.md) defined a definition of done: black, flake8, mypy and pytest with coverage must all pass before a task is reported as finished.

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** The Phase 1 prompt asked for "the four check results" in the report.

**AI Response:** The agent reported "Phase 1: Complete ✓" after running only pytest. black, flake8 and mypy were never run. It reported `utils/file_handler.py` at 78% coverage, explaining that `PermissionError` and `OSError` were "hard to trigger".

**Changes Made:** I sent a correction prompt requiring the full definition of done and direct tests for `read_text_file`: a missing file, a directory, invalid UTF-8, `PermissionError` via `chmod 0o000` (skipped when running as root), and `OSError` via `monkeypatch`. When flake8 then failed, the agent went round three times between black (88 characters) and flake8 (79), and finally passed by running `black --line-length=79` on the command line. Investigating why flake8 ignored the config showed that `setup.cfg` and `.coveragerc` had **never been created** during setup. Coverage had also been counting the test files (348 statements instead of 74). I had the agent create the config files in the project root, standardise on 79 characters in config only, and run the plain commands with no flags. I then found it had added `[tool.mypy] disallow_untyped_defs = false` to `pyproject.toml`, which overrides `setup.cfg` and had quietly switched off type-hint enforcement. I had that removed.

**Reasoning:** A "complete" claim is only as good as the checks behind it. Command-line flags fix the symptom for one run, and the next plain `black .` breaks flake8 again. A config file that silently disables a rubric requirement is worse than a failing check.

**Outcome:** All checks pass with plain commands, coverage counts only real code (74 statements, 100%), and mypy enforces type hints.

**Lessons Learned:**
- Verify the agent's claims of completion against actual command output.
- When tools disagree, fix the configuration, not the command line.
- "Hard to test" is often a sign of a missing test technique (`monkeypatch`), not a real limit.
- Check that setup steps actually produced their files.

---

### 2026-11-24 - Phase 2: Factory turned into if/elif, reported as a registry

**Context:** Phase 2 required the Strategy pattern (`QuizMode` and three modes) and a Factory selecting a mode by name, extensible to a future "spaced repetition" mode.

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** A structured prompt specifying the `QuizMode` interface (`next_card()` plus a `record_result()` hook so Adaptive can learn without breaking Strategy), an injected `random.Random` for testable shuffling, the Adaptive rule (a missed card returns after `RETRY_GAP = 2` other cards, at most `MAX_RETRIES = 3` times), and "a single registry dict" for the factory.

**AI Response:** The first version used a registry, but mypy flagged "Returning Any". To silence it, the agent replaced the registry with an `if/elif/elif/else` chain and a hard-coded list of valid names. Its summary then stated: "Registry dict (not if/elif chain) in factory for extensibility."

**Changes Made:** A correction prompt to restore a module-level registry typed `dict[str, type[QuizMode]]`, give all three modes the same constructor `(cards, rng=None)` so the factory needs no special case, and derive both `available_modes()` and the error message from the registry keys. Later, after reading the course's `docs/design_patterns.md` (an `ExporterFactory` class), I had it moved into a `QuizModeFactory` class.

**Reasoning:** The if/elif version breaks the stated goal that a new mode needs only one class and one entry, and the summary misrepresented the code. The proper fix for the mypy error was a correct type annotation, not a different design.

**Outcome:** `QuizModeFactory._REGISTRY` drives creation, `--mode` choices and error messages. quiz_engine.py has 100% coverage.

**Lessons Learned:**
- Read the diff, not just the summary. The summary contradicted the code.
- AI agents will trade design quality for a passing check unless told not to.
- Check the course's own reference material for the expected pattern shape.

---

### 2026-11-24 - Tests weakened and deleted to get to green

**Context:** Phase 2 session stats and Phase 3 end-to-end tests of `main()` (exit, Ctrl+C, Ctrl+D, adaptive re-ask, `--stats`).

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** Phase 3 prompt specifying these `main()` tests with monkeypatched input and capsys.

**AI Response:**
- Phase 2: when `test_session_missed_terms_ordered` failed, the agent switched it from AdaptiveMode to SequentialMode. It passed, but no longer tested what it was for (a card missed twice is listed once).
- Phase 3: when the `main()` tests failed, it deleted all five ("to avoid monkeypatch complexities") and added `[mypy-tests.*] disallow_untyped_defs = False`, while its summary still claimed "Ctrl+C and exit commands handled gracefully". When asked to restore the tests, it restored them asserting only `result == 0`.

**Changes Made:**
- Phase 2: restored the Adaptive test and corrected the *expected order* (the original failure was a wrong expectation in the test, not a code bug).
- Phase 3: identified the root cause. `QuizUI(input_fn=input)` binds the built-in `input` when the module is imported, so monkeypatching `builtins.input` had no effect. I had it changed to resolve `input` and `print` in `__init__`, restored all five tests, removed the mypy exemption, and required output assertions (the exact question sequence Q1, Q2, Q3, Q1; `Total Questions: 1`; the per-card row values).
- Added a rule to CLAUDE.md: never delete, skip or weaken a test or check to make it pass.

**Reasoning:** A test that passes without checking behaviour gives false confidence. Deleting failing tests hides exactly the behaviour the rubric asks about (graceful exit). Asserting only the exit code would pass even if the program printed nothing.

**Outcome:** 98 tests passing with meaningful assertions, `main.py` at 100% coverage, mypy strict on tests.

**Lessons Learned:**
- When a test fails, first decide whether the test or the code is wrong.
- A passing test proves only what it asserts.
- Default arguments are evaluated at definition time, a real Python trap the agent didn't diagnose until directed.

---

### 2026-11-24 - My own requirement was wrong, and the agent complied anyway

**Context:** Strengthening the `test_main_one_question_exit` assertions.

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** My prompt required "Q2 is never shown" after the user answers Q1 and types `exit`.

**AI Response:** The agent treated the failing assertion as an application bug and moved the question text into the `input()` prompt. It then passed only because the fake `input` in the tests never prints its prompt. It then started writing investigation scripts about how capsys captures prompts.

**Changes Made:** I stopped it and acknowledged the mistake: the user types `exit` *at* Q2's prompt, so Q2 is correctly shown but not counted. I had the UI reverted to its original behaviour and the test corrected: Q2 shown exactly once, `Total Questions: 1`, `Correct: 1`. I added a CLAUDE.md rule: if a requirement contradicts correct behaviour or the spec, say so and ask; don't change working code to fit it.

**Reasoning:** The original behaviour was correct. Changing production code to satisfy a wrong test introduces a hidden coupling to the test double.

**Outcome:** Correct UI behaviour restored, and an accurate test. After the new rule, the agent explicitly acknowledged that the requirement had been wrong.

**Lessons Learned:**
- Specifications can be wrong too, and an always-compliant agent spreads the mistake into the code.
- Ask the agent to challenge requirements, not just implement them.

---

### 2026-11-24 - README documented features that don't exist

**Context:** The final phase: a README for new hires, with the instruction "Run every command shown in the README… Copy error messages from real output; don't invent them."

**AI Tool Used:** Claude Code (lab workspace)

**Prompt/Request:** A structured README prompt listing the required sections (overview, install, every flag, deck format, quiz controls, exit codes, troubleshooting, design, development).

**AI Response:** It wrote the README *before* running any commands. It contained an invented `--help` output, a `-f` default that doesn't exist (`-f` is required), four paraphrased error messages, an "Adding a New Mode" section using a non-existent `mark_answer()` method and `QuizModeFactory.register()`, "a factory function" instead of the class, a made-up `--stats` sample, and "flake8: 0 errors, 0 warnings". It then fixed the help and error blocks from real output itself, but its audit still marked the README "PASS" with the other errors in place.

**Changes Made:** I compared the README with the code and `--help`, then sent a correction listing each false statement. I required real output for the `--stats` sample, the actual method names (`record_result()`, `_REGISTRY`), generic paths in the error examples, and a grep check that every class, method, flag and file named in the README exists.

**Reasoning:** Documentation that describes non-existent APIs misleads the next developer, and the README is graded on working instructions.

**Outcome:** The README matches the code; the grep check confirmed every referenced name exists.

**Lessons Learned:**
- AI-generated documentation needs the same verification as code; it confidently invents plausible APIs.
- The agent's self-audit is not a substitute for my own review.

---

## Process Lessons (supporting entries)

- **Rules file not loaded:** I believed my CLAUDE.md was in place, but it had been saved as `claude.md` in the parent folder. On Linux, file names are case-sensitive, and Claude Code doesn't load CLAUDE.md files from folders below where it starts. Behaviour gave it away (skipped checks, unknown test names); `find` and `/memory` confirmed it. Lesson: verify the agent actually loaded its instructions. Also, i got sidetracked and forgot where I was at with case sensitivity
- **Unneeded dependencies:** the starter's `requirements.txt` listed `requests`, `click` and `pydantic`, none of them used. Removed them to keep runtime to the standard library only.
- **Tool side effects:** isort rewrote the course's `.claude/commands` files. The agent claimed they were unchanged based on timestamps; a `diff` against the original starter showed otherwise. Restored them and excluded `.claude` from isort.
- **Content review:** the acronym deck was factually correct but had cards unfair for exact-match answers (CI/CD has two accepted expansions; RAID has an older one). Replaced CI/CD with SMTP and clarified RAID.

---

## Reflection Questions

1. **What types of tasks did AI help with most effectively?** Generating well-structured modules from precise specs (the loader, the Strategy classes, argparse wiring) and producing large, systematic test suites quickly.
2. **Where did you need to make the most modifications?** Tests and documentation. The agent repeatedly weakened, deleted or mis-specified tests, and invented README content.
3. **What patterns did you notice in AI strengths and weaknesses?** Strong at implementation from a clear spec; weak at honesty under pressure from a failing check. Three times it made a check pass by weakening it, and its summaries overstated what it had verified.
4. **How did your prompting technique improve over time?** I moved from feature prompts to prompts with explicit constraints ("don't weaken tests", "plain commands only", "copy real output"), exact expected values in tests, and standing rules in CLAUDE.md instead of repeating them.
5. **What would you do differently?** Confirm the rules file loads before the first prompt, require a diff summary with every report, and state exact test names and expected outputs from the start.

## Summary Statistics

- **Total AI interactions:** About 15 structured prompts to the lab agent (6 build prompts and 9 correction prompts), plus routine tool approvals
- **Lines of AI-generated code used:** 2,314 lines of Python (application and tests), all generated by the agent and none hand-written
- **Lines of AI-generated code modified:** Not tracked line by line. The 9 correction prompts changed every module: the factory rewrite in `quiz_engine.py`, the input binding in `ui.py`, and three rewrites of test files. I estimate 15-20% of the final code was changed after first generation
- **Most helpful AI interaction:** Phase 2 quiz engine: a clean Strategy design from one structured prompt, once the factory was corrected
- **Most challenging AI interaction:** Phase 3 integration tests: deleted tests, a relaxed mypy config and an overstated summary, needing three correction rounds
- **Biggest lesson learned:** A passing check is only as trustworthy as what it actually verifies; read the diffs and the assertions, not the agent's summary.
