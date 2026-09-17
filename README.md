# 42 Examshell for Windows

Practice the **42 Exam Rank 02** at home on Windows — **no Linux, no VM, no WSL**. Just Python and gcc.

examshell is a local exam shell with all **56 exercises of levels 1–4**, a grader that compiles your
code and compares it against reference solutions, and three learning modes that teach you the tricky
parts of every exercise.

```
   1  Exam mode      levels 1 -> 4 with a timer, unlimited retries with the trace
   2  Practice mode  choose any exercise, retry as often as you want
   3  Fill the gap   complete the key lines of a solution and learn why they work
   4  Find the bug   read the grader's trace, find the broken line, fix it
   5  Predict        type the exact output for tricky inputs (spaces, newlines, argc...)
   6  Loop mode      every exercise of one level, one after another
   q  Quit
```

```
[02:41:07] L4 examshell> grademe

>>>>>>>>>>>>>>>>>>>>>>>>>>>> FAILURE <<<<<<<<<<<<<<<<<<<<<<<<<<<<
  Wrong output
  Test 2/27: ./rostring "Que la      lumiere soit et la lumiere fut"
  expected: la lumiere soit et la lumiere fut Que$
  yours   : la      lumiere soit et la lumiere fut Que$
  trace: exam\2026-09-15_18-30-44\traces\02-rostring.trace

  Not yet (1 failed try on rostring). Read the trace above, fix your code and type grademe again.
```

## Quick start

**1. Install Python and gcc** (once). Open a terminal (PowerShell or cmd) and run:

```
winget install Python.Python.3.12
winget install BrechtSanders.WinLibs.POSIX.UCRT
```

Then **close the terminal and open a new one**, so Windows picks up the new programs.

**2. Get examshell:**

```
git clone https://github.com/NeonLp101/42-examshell-windows.git
```

or download the ZIP (green *Code* button → *Download ZIP*) and extract it.

**3. Check the setup:**

```
examshell.bat check
```

It compiles and grades two reference solutions. If it says *Everything works*, you're ready.

**4. Start it:** double-click **`examshell.bat`** (or run it from the terminal).

### Troubleshooting

- **"Windows protected your PC"** when starting the .bat: click *More info* → *Run anyway*. For a
  downloaded ZIP you can also right-click the ZIP → *Properties* → *Unblock* before extracting.
- **"No C compiler found"**: open a *new* terminal after installing gcc. Or set the environment
  variable `EXAMSHELL_CC` to the full path of `gcc.exe`.
- **"Python was not found; run without arguments to install from the Microsoft Store"**: that's a
  Windows placeholder, not Python. Install Python with the winget command above.

## Modes

### Exam
Like the real Exam Rank 02. You start at level 1 with a random assignment and a timer (180 min).
When `grademe` passes, you move on to the next level (25 points per level). When it fails, you see
the trace — the failing test, the expected output and yours — and keep the same assignment: fix it
and `grademe` again, as often as you want.

- `examshell.bat exam 3` practices a single level; `examshell.bat exam 4 90` sets the duration.
- `exit` keeps the exam running, so you can resume it later from the menu.
- `pause` stops the clock when you need a break (food, a call...). Enter continues with exactly the
  time you had left — you can even close the window while paused. Paused time is shown in `status`
  and in the history. The real exam has no pause, so use it for practice runs.
- Each session is kept in `exam\<date>\` (subjects, rendu, traces), and results go to `exam\history.log`.

### Loop mode
Go through **every exercise of one level**, one after another, in random order. Same flow as the
exam: `grademe`, the trace on failure, unlimited retries. Passing brings the next exercise, and the
loop is done when you've passed them all.

- `skip` moves the current exercise to the end of the loop, if you want to come back to it later.
- No time limit by default: `examshell.bat loop 4` loops through level 4, `examshell.bat loop 4 120`
  adds a 120 minute timer.
- `pause` stops the clock, `exit` keeps the loop running; resume it from the menu.

### Practice
Any exercise, any level, no timer. Progress is saved.
- `list` shows all exercises grouped by level (`list 2` shows only level 2)
- `pick <name|#>` switches exercise, `next 3` picks a random level-3 exercise you haven't passed
- your code goes in `practice\rendu\<exercise>\`

### Fill the gap
A real solution with holes in its most important lines. Type what goes in each hole (spacing doesn't
matter). Common mistakes get specific feedback, e.g. `tab[cur.x][cur.y]` → *"x and y are swapped:
tab[row][column] = tab[y][x]"*. After each gap, **WHY** explains the syntax and the idea behind it:
what `(t_point){x, y}` is, why `ft_list_remove_if` takes a `t_list **`, why `ft_itoa` needs a
`long`... At the end you see the complete solution, a summary and your score — then `p` takes you to
practice mode to write it from scratch. 209 gaps across all 56 exercises.

In a gap: `?` hint · `!` show the answer · `:code` whole file · `:q` quit

### Find the bug
A solution that compiles but **fails**. You get the grader's trace and the code:
1. type the line number of the bug
2. type the corrected line — it's checked by the real grader, so any correct fix counts

Then you learn what the bug was and why. 328 bugs, all verified to fail at runtime.

### Predict the output
Tricky inputs — extra spaces, tabs, wrong argument count, empty strings, INT_MIN... You type the exact
output (program output the way `cat -e` shows it: `$` marks the end of the line), then read why.
Most exam failures come from details like these, not from the algorithm. 220 questions.

## Commands

| command | what it does |
|---------|--------------|
| `grademe` | grade the current assignment |
| `status`  | assignment, level, folders, time left |
| `subject` | print the subject |
| `open` / `code` | open your rendu folder in Explorer / VS Code |
| `list [level]`, `pick`, `next [level]` | practice mode: choose exercises |
| `learn`, `bugs`, `predict` | practice mode: learning modes for the current exercise |
| `skip` | loop mode: move the current exercise to the end of the loop |
| `pause` | exam / loop mode: stop the clock until you press Enter |
| `finish` | exam / loop mode: give up |
| `exit` | back to the menu |

Command line shortcuts: `examshell.bat loop 4`, `examshell.bat practice ft_split`, `examshell.bat gaps flood_fill`,
`examshell.bat bugs rostring`, `examshell.bat predict ft_itoa`, and
`examshell.bat grade <exercise> <folder>` to grade any folder once.

## How grading works

1. The expected files must be in `rendu\<exercise>\` (e.g. `ft_list_foreach` also needs `ft_list.h`).
2. **Forbidden functions**: calling anything that isn't in the subject's "Allowed functions" (and
   isn't defined by you) fails.
3. Your code is compiled with `gcc -Wall -Wextra -Werror -std=gnu17`. For function exercises the grader
   uses its own `main` — remove yours.
4. Your output is compared byte for byte with a reference solution: fixed edge cases (including
   every example from the subject) plus random tests. Crashes and infinite loops (> 5 s) fail.
5. On failure you see the first failing test; the full trace is saved in `traces\`.

Windows differs from the Linux exam machines in a few ways — examshell compensates so that code that
is correct on Linux also passes here:
- `long` is 32-bit on Windows: it's treated as 64-bit, like on Linux (the usual `ft_itoa` needs it)
- output is compared without Windows `\r\n` line endings
- arguments are not wildcard-expanded
- programs get an 8 MB stack, like on Linux (deep recursion in `flood_fill`)
- code is compiled as C17 — newer gcc defaults to C23, which breaks `int (*cmp)()`

## Limitations

- The tests are written to match the subjects, but they are **not the official 42 tests**. Passing
  here makes passing the exam likely, not certain.
- Memory leaks can't be checked (there is no valgrind on Windows).
- The real exam machines use a Linux terminal with vim/emacs — practice without VS Code sometimes too.

## About the reference solutions

The reference solutions are in `exercises\level*\*\ref\` — the grader needs them. Looking at them
before you've solved an exercise yourself defeats the purpose: use *Fill the gap* when you're stuck,
it explains instead of just showing.

## Adding or fixing exercises

Exercises, tests, lessons and quizzes are plain files — see [docs/exercise-format.md](docs/exercise-format.md).
Found a test that rejects a correct solution? Open an issue with the trace.

## Credits & license

- Exercise subjects from [alexhiguera/Exam_Rank_02_42_School](https://github.com/alexhiguera/Exam_Rank_02_42_School) (MIT) — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Not affiliated with or endorsed by 42.
- examshell itself is released under the [MIT License](LICENSE).
