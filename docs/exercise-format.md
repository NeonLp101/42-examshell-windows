# Exercise format

Every exercise is a folder `exercises/level<N>/<name>/`. examshell finds exercises automatically by
their `config.json` — adding a folder is enough to add an exercise.

```
exercises/level2/ft_strdup/
├── config.json        how to grade it
├── subject.en.txt     the subject shown to the student
├── ref/               reference solution (the expected output comes from it)
│   └── ft_strdup.c
├── tester/main.c      function exercises only: the grader's main()
├── attach/            files given to the student (e.g. list.h), optional
├── gaps.txt           "Fill the gap" lesson, optional
└── predict.txt        "Predict the output" quiz, optional
```

## config.json

```json
{
  "type": "program",
  "expected_files": ["rostring.c"],
  "allowed_functions": ["write", "malloc", "free"],
  "fixed_tests": [["abc   "], [], ["first", "2", "11000000"]],
  "generator": "words_messy",
  "random_tests": 15
}
```

| field | meaning |
|-------|---------|
| `type` | `"program"` (has its own `main`) or `"function"` (graded with `tester/main.c`) |
| `expected_files` | files the student must turn in; patterns like `"*.c"` are allowed |
| `allowed_functions` | anything else the student calls (and doesn't define) is a forbidden function |
| `fixed_tests` | programs: list of argument lists, always run first |
| `generator` / `random_tests` | programs: name of a random-argument generator in `examshell.py` (`GENERATORS`) and how many random tests to run |
| `seeds` | functions: `tester/main.c` is run with seed 0 (fixed edge cases) and seeds 1..N (random tests) |
| `attachments` | files from `attach/` copied next to the student's code and into the subject folder |

A test passes when the student's output is byte-for-byte identical to the reference solution's
output for the same arguments (or seed). A crash or a run longer than 5 seconds fails.

## tester/main.c (function exercises)

A normal C file with a `main(int argc, char **argv)`:

- `argv[1]` is the seed. Seed `0` runs the hand-picked edge cases, other seeds generate random inputs
  (always use your own deterministic RNG so the reference and the student get identical inputs).
- Print every call and its result on its own line, e.g. `ft_strlen("abc") = 3`. When a test fails,
  the student sees the first line that differs.
- Call `fflush(stdout)` before calling the student's function, so the output before a crash is kept.
- All helper functions must be `static` (they must not clash with the student's functions) and the
  file must compile with `-Wall -Wextra -Werror -std=gnu17`.

## gaps.txt ("Fill the gap")

```
@@ intro
Text shown before the code. Lines indented by 4 spaces are shown as code,
`backticks` are highlighted, "- " starts a list item.

@@ file ft_strlen.c
int	ft_strlen(char *str)
{
	int	i;

	i = {{1}};
	while ({{2}})
		i++;
	return (i);
}

@@ gap 1
answer: 0
wrong: 1 => Off by one: "" must return 0.
hint: What must ft_strlen("") return?
The explanation shown after the gap (same markup as the intro).

@@ gap 2
...

@@ outro
The "big picture" summary shown at the end.
```

- `{{n}}` marks a gap; gaps are asked in the order they appear. A file can contain several `@@ file`
  sections (e.g. a header and a `.c` file) — together they must be a complete, correct solution.
- Answers are compared token by token (spacing doesn't matter). Every `accept:` must be an answer
  that also produces a correct solution when put in the gap.
- `wrong: <answer> => <feedback>` gives specific feedback for a common mistake. Wrong answers that
  compile but fail the tests automatically become **Find the bug** puzzles.

## predict.txt ("Predict the output")

```
@@ question
match: exact
args: ["abc   "]
answer: abc$
wrong: abc   $ => Trailing blanks are not printed.
    $> ./rostring "abc   " | cat -e
---
The explanation shown after the question.
```

| field | meaning |
|-------|---------|
| `answer` / `accept` | the expected answer and alternatives |
| `match` | `tokens` (default, spacing ignored), `exact` (program output written like `cat -e`, spaces matter) or `text` (case-insensitive words) |
| `args` | optional: program arguments. Not used by examshell itself, but lets you verify the answer against the reference solution |
| `wrong` | `<answer> => <feedback>` for common mistakes |

Everything before `---` is the question, everything after it the explanation.

## bug_cache.json

`exercises/bug_cache.json` stores whether each wrong answer of every lesson compiles and fails at
runtime, so **Find the bug** doesn't have to grade them at startup. It's keyed by a hash of the buggy
code and the tester, so stale entries are simply ignored; missing entries are computed (and saved)
the first time a puzzle is played.

## Checking your changes

```
examshell.bat grade <exercise> exercises\level<N>\<exercise>\ref
```

must print SUCCESS. Then play the lesson (`examshell.bat gaps <exercise>`) and the quiz
(`examshell.bat predict <exercise>`) once.
