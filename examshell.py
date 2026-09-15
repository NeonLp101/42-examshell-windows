#!/usr/bin/env python3
"""
examshell - practice the 42 Exam Rank 02 (levels 1-4) locally on Windows.

    examshell.bat                         main menu
    examshell.bat exam [level] [minutes]  start / resume an exam (no level = levels 1 -> 4)
    examshell.bat practice [exercise]     practice mode
    examshell.bat gaps [exercise]         fill the gap (learn the key lines)
    examshell.bat bugs [exercise]         find the bug
    examshell.bat predict [exercise]      predict the output
    examshell.bat grade <exercise> <dir>  grade a folder once (no shell)
    examshell.bat check                   check that Python and gcc are set up correctly

Needs Python 3.8+ and gcc (MinGW-w64: winget install BrechtSanders.WinLibs.POSIX.UCRT).
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print("examshell needs Python 3.8 or newer (you have %d.%d)." % sys.version_info[:2])
    print("Install it from https://www.python.org/downloads/ or run:  winget install Python.Python.3.12")
    sys.exit(1)

import bisect
import hashlib
import json
import os
import random
import re
import shutil
import string
import textwrap
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXERCISES_DIR = ROOT / "exercises"
PRACTICE_DIR = ROOT / "practice"
EXAM_DIR = ROOT / "exam"
BUILD_DIR = Path(tempfile.gettempdir()) / "examshell_build"

IS_WINDOWS = os.name == "nt"
EXE_SUFFIX = ".exe" if IS_WINDOWS else ""
CFLAGS = ["-Wall", "-Wextra", "-Werror", "-std=gnu17"]
# Linux gives programs an 8 MB stack, Windows only 1 MB: match Linux so recursive
# solutions (flood_fill) behave like they would on the exam machines.
LDFLAGS = ["-Wl,--stack,8388608"] if IS_WINDOWS else []
RUN_TIMEOUT = 5
DEFAULT_EXAM_MINUTES = 60      # one level
FULL_EXAM_MINUTES = 180        # levels 1 -> 4, like the real exam


# --------------------------------------------------------------------------- #
#  Terminal helpers
# --------------------------------------------------------------------------- #

class C:
    RESET = BOLD = DIM = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = ""


def enable_colors() -> None:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return
    if IS_WINDOWS:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return
            if not kernel32.SetConsoleMode(handle, mode.value | 0x0004):
                return
        except Exception:
            return
    C.RESET, C.BOLD, C.DIM = "\033[0m", "\033[1m", "\033[2m"
    C.RED, C.GREEN, C.YELLOW = "\033[91m", "\033[92m", "\033[93m"
    C.BLUE, C.MAGENTA, C.CYAN = "\033[94m", "\033[95m", "\033[96m"


def silence_crash_dialogs() -> None:
    """Crashing test binaries must not pop up 'program stopped working' windows."""
    if IS_WINDOWS:
        try:
            import ctypes
            # SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX
            ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
        except Exception:
            pass


def clear_screen() -> None:
    os.system("cls" if IS_WINDOWS else "clear")


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def confirm(prompt: str) -> bool:
    return ask(f"{prompt} {C.DIM}(y/n){C.RESET} ").lower() in ("y", "yes")


def fmt_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


BANNER_GLYPHS = {
    "E": [" ___ ", "| __|", "| _| ", "|___|"],
    "X": ["__  __", "\\ \\/ /", " >  < ", "/_/\\_\\"],
    "A": ["   _   ", "  /_\\  ", " / _ \\ ", "/_/ \\_\\"],
    "M": [" __  __ ", "|  \\/  |", "| |\\/| |", "|_|  |_|"],
    "S": [" ___ ", "/ __|", "\\__ \\", "|___/"],
    "H": [" _  _ ", "| || |", "| __ |", "|_||_|"],
    "L": [" _    ", "| |   ", "| |__ ", "|____|"],
}


def print_banner(subtitle: str = "") -> None:
    rows = ["".join(BANNER_GLYPHS[ch][r] for ch in "EXAMSHELL") for r in range(4)]
    print()
    for row in rows:
        print(f"  {C.CYAN}{C.BOLD}{row}{C.RESET}")
    print(f"  {C.DIM}Exam Rank 02 - local practice shell for Windows{C.RESET}")
    if subtitle:
        print(f"  {subtitle}")
    print()


def rule(title: str = "") -> None:
    if title:
        print(f"{C.DIM}----- {C.RESET}{C.BOLD}{title}{C.RESET} {C.DIM}{'-' * max(3, 66 - len(title))}{C.RESET}")
    else:
        print(f"{C.DIM}{'-' * 74}{C.RESET}")


# --------------------------------------------------------------------------- #
#  Exercises
# --------------------------------------------------------------------------- #

@dataclass
class Exercise:
    name: str
    level: int
    path: Path
    kind: str                       # "program" or "function"
    expected_files: list
    allowed_functions: list
    attachments: list
    seeds: int
    fixed_tests: list
    generator: str
    random_tests: int

    @property
    def subject(self) -> str:
        return (self.path / "subject.en.txt").read_text(encoding="utf-8")


def load_exercises() -> list:
    exercises = []
    for cfg_path in sorted(EXERCISES_DIR.glob("level*/*/config.json")):
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        ex_dir = cfg_path.parent
        exercises.append(Exercise(
            name=ex_dir.name,
            level=int(ex_dir.parent.name.replace("level", "")),
            path=ex_dir,
            kind=cfg["type"],
            expected_files=cfg["expected_files"],
            allowed_functions=cfg.get("allowed_functions", []),
            attachments=cfg.get("attachments", []),
            seeds=cfg.get("seeds", 10),
            fixed_tests=cfg.get("fixed_tests", []),
            generator=cfg.get("generator", ""),
            random_tests=cfg.get("random_tests", 0),
        ))
    return exercises


# Random argument generators for program exercises.
WORD_CHARS = string.ascii_letters + string.digits + ".,!?'-_*:;()"
SMALL_PRIMES = [p for p in range(2, 1000) if all(p % d for d in range(2, int(p ** 0.5) + 1))]


def _word(rng: random.Random, lo: int = 1, hi: int = 8) -> str:
    return "".join(rng.choice(WORD_CHARS) for _ in range(rng.randint(lo, hi)))


def gen_fprime(rng: random.Random) -> list:
    r = rng.random()
    if r < 0.3:
        n = rng.randint(1, 1000)
    elif r < 0.6:
        n = rng.randint(1, 1_000_000)
    else:
        n = 1
        while True:
            p = rng.choice(SMALL_PRIMES)
            if n * p > 2_000_000_000:
                break
            n *= p
            if rng.random() < 0.15:
                break
    return [str(n)]


def gen_words_single_space(rng: random.Random) -> list:
    return [" ".join(_word(rng) for _ in range(rng.randint(1, 8)))]


def gen_words_messy(rng: random.Random) -> list:
    def blanks(lo: int) -> str:
        return "".join("\t" if rng.random() < 0.25 else " " for _ in range(rng.randint(lo, 4)))

    words = [_word(rng) for _ in range(rng.randint(0, 7))]
    args = [blanks(0) + "".join(w + blanks(1) for w in words[:-1]) + (words[-1] if words else "") + blanks(0)]
    if rng.random() < 0.2:
        args += [_word(rng) for _ in range(rng.randint(1, 3))]
    return args


TEXT_CHARS = string.ascii_letters + string.digits + "     .,!?'-_*:;()@[`{"


def _text(rng: random.Random, lo: int = 0, hi: int = 40, charset: str = TEXT_CHARS) -> str:
    return "".join(rng.choice(charset) for _ in range(rng.randint(lo, hi)))


def gen_text(rng: random.Random) -> list:
    return [_text(rng) + ("\t" + _text(rng, 0, 5) if rng.random() < 0.15 else "")]


def gen_search_replace(rng: random.Random) -> list:
    s = _text(rng, 1, 30)
    find = rng.choice(s) if rng.random() < 0.8 else rng.choice(string.ascii_letters)
    return [s, find, rng.choice(string.ascii_letters + string.digits)]


def _lower_words(rng: random.Random, lo: int = 1, hi: int = 5) -> list:
    return ["".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 7)))
            for _ in range(rng.randint(lo, hi))]


def gen_camel(rng: random.Random) -> list:
    words = _lower_words(rng)
    return [words[0] + "".join(w.capitalize() for w in words[1:])]


def gen_snake(rng: random.Random) -> list:
    return ["_".join(_lower_words(rng))]


def gen_do_op(rng: random.Random) -> list:
    op = rng.choice("+-*/%")
    if op == "*":
        a, b = rng.randint(-46340, 46340), rng.randint(-46340, 46340)
    elif op in "+-":
        a, b = rng.randint(-1_000_000_000, 1_000_000_000), rng.randint(-1_000_000_000, 1_000_000_000)
    else:
        a, b = rng.randint(-1_000_000, 1_000_000), rng.choice([-1, 1]) * rng.randint(1, 1000)
    return [str(a), op, str(b)]


def gen_two_strings(rng: random.Random) -> list:
    s2 = _text(rng, 0, 30, "abcdefgh 123")
    if s2 and rng.random() < 0.5:
        s1 = "".join(c for c in s2 if rng.random() < 0.3)
    else:
        s1 = _text(rng, 0, 6, "abcdefgh 123")
    return [s1, s2]


def gen_add_prime_sum(rng: random.Random) -> list:
    return [str(rng.randint(1, 3000))]


def gen_paramsum(rng: random.Random) -> list:
    return [_word(rng) for _ in range(rng.randint(0, 12))]


def gen_pgcd(rng: random.Random) -> list:
    g = rng.randint(1, 500)
    return [str(g * rng.randint(1, 2000)), str(g * rng.randint(1, 2000))]


def gen_print_hex(rng: random.Random) -> list:
    return [str(rng.randint(0, 300) if rng.random() < 0.3 else rng.randint(0, 2**31 - 1))]


def gen_capitalizer(rng: random.Random) -> list:
    def arg() -> str:
        words = ["".join(rng.choice(string.ascii_letters + string.digits + ".,!_-") for _ in range(rng.randint(1, 8)))
                 for _ in range(rng.randint(0, 6))]
        seps = lambda lo: "".join(rng.choice(" \t ") for _ in range(rng.randint(lo, 3)))  # noqa: E731
        return seps(0) + "".join(w + seps(1) for w in words[:-1]) + (words[-1] if words else "") + seps(0)
    return [arg() for _ in range(rng.randint(1, 3))]


def gen_tab_mult(rng: random.Random) -> list:
    return [str(rng.randint(1, 1000) if rng.random() < 0.5 else rng.randint(1, 238609294))]


GENERATORS = {
    "fprime": gen_fprime,
    "words_single_space": gen_words_single_space,
    "words_messy": gen_words_messy,
    "text": gen_text,
    "search_replace": gen_search_replace,
    "camel": gen_camel,
    "snake": gen_snake,
    "do_op": gen_do_op,
    "two_strings": gen_two_strings,
    "add_prime_sum": gen_add_prime_sum,
    "paramsum": gen_paramsum,
    "pgcd": gen_pgcd,
    "print_hex": gen_print_hex,
    "capitalizer": gen_capitalizer,
    "tab_mult": gen_tab_mult,
}


# --------------------------------------------------------------------------- #
#  C source analysis
# --------------------------------------------------------------------------- #

TOKEN_RE = re.compile(r"[A-Za-z_]\w*|->|\S")
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double",
    "else", "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long",
    "register", "restrict", "return", "short", "signed", "sizeof", "static", "struct",
    "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "_Bool",
    "bool", "_Alignof", "alignof", "_Generic", "_Static_assert", "static_assert",
    "__attribute__", "__typeof__", "typeof", "__extension__", "__inline", "__restrict",
    "offsetof", "va_start", "va_arg", "va_end", "va_copy",
}
TYPE_WORDS = {
    "void", "char", "short", "int", "long", "float", "double", "signed", "unsigned",
    "const", "struct", "union", "enum", "static", "extern", "size_t", "ssize_t",
}


def _blank(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def strip_c_source(src: str):
    """Blank out comments, string/char literals and preprocessor lines.

    The result has exactly the same length as `src` (offsets and line numbers
    stay valid). Also returns the names of all macros defined in the file.
    """
    out = []
    macros = set()
    i, n = 0, len(src)
    line_start = True
    while i < n:
        c = src[i]
        if c == "#" and line_start:
            j = i
            while j < n and not (src[j] == "\n" and src[j - 1] != "\\" and src[max(0, j - 2):j] != "\\\r"):
                j += 1
            m = re.match(r"#\s*define\s+([A-Za-z_]\w*)", src[i:j])
            if m:
                macros.add(m.group(1))
            out.append(_blank(src[i:j]))
            i = j
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(_blank(src[i:j]))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(_blank(src[i:j]))
            i = j
            line_start = False
            continue
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j, n)
            out.append(c)
            out.append(_blank(src[i + 1:j]))
            if j < n and src[j] == c:
                out.append(c)
                j += 1
            i = j
            line_start = False
            continue
        if c == "\n":
            line_start = True
        elif c not in " \t\r\f\v":
            line_start = False
        out.append(c)
        i += 1
    return "".join(out), macros


def _matching_paren(tokens: list, open_idx: int):
    depth = 0
    for k in range(open_idx, len(tokens)):
        if tokens[k][0] == "(":
            depth += 1
        elif tokens[k][0] == ")":
            depth -= 1
            if depth == 0:
                return k
    return None


def find_forbidden_calls(sources: dict, allowed: list) -> list:
    """Return [(function, file, line)] for calls to functions that are neither
    allowed by the subject nor defined by the student."""
    known = set(allowed)
    calls = []
    for fname, src in sources.items():
        code, macros = strip_c_source(src)
        known |= macros
        line_starts = [0] + [m.end() for m in re.finditer("\n", code)]
        tokens = [(m.group(), bisect.bisect_right(line_starts, m.start()))
                  for m in TOKEN_RE.finditer(code)]
        # function pointer declarators: ( * name ) (
        for k in range(len(tokens) - 4):
            if (tokens[k][0] == "(" and tokens[k + 1][0] == "*" and IDENT_RE.fullmatch(tokens[k + 2][0])
                    and tokens[k + 3][0] == ")" and tokens[k + 4][0] == "("):
                known.add(tokens[k + 2][0])
        depth = 0
        for k, (tok, line) in enumerate(tokens):
            if tok == "{":
                depth += 1
                continue
            if tok == "}":
                depth = max(0, depth - 1)
                continue
            if tok in C_KEYWORDS or not IDENT_RE.fullmatch(tok):
                continue
            if k + 1 >= len(tokens) or tokens[k + 1][0] != "(":
                continue
            prev = tokens[k - 1][0] if k else ""
            if prev in (".", "->"):
                continue
            close = _matching_paren(tokens, k + 1)
            if depth == 0:
                if close is not None and close + 1 < len(tokens) and tokens[close + 1][0] == "{":
                    known.add(tok)
                    # parameter names (e.g. a function-typed parameter) are callable too
                    known.update(t for t, _ in tokens[k + 2:close] if IDENT_RE.fullmatch(t))
                continue
            if prev in TYPE_WORDS:
                continue  # local prototype, not a call
            calls.append((tok, fname, line))
    seen = set()
    forbidden = []
    for name, fname, line in calls:
        if name not in known and name not in seen:
            seen.add(name)
            forbidden.append((name, fname, line))
    return forbidden


def widen_long(src: str):
    """On Windows `long` is 32 bits, on the exam machines (Linux) it is 64 bits.
    Rewrite a lone `long` into `long long` so solutions that rely on it (ft_itoa
    with INT_MIN...) behave like on Linux. Returns (new_source, changed)."""
    code, _ = strip_c_source(src)
    tokens = [(m.group(), m.end()) for m in TOKEN_RE.finditer(code)]
    inserts = []
    k = 0
    while k < len(tokens):
        if tokens[k][0] != "long":
            k += 1
            continue
        j = k
        while j + 1 < len(tokens) and tokens[j + 1][0] == "long":
            j += 1
        following = tokens[j + 1][0] if j + 1 < len(tokens) else ""
        if j == k and following != "double":
            inserts.append(tokens[k][1])
        k = j + 1
    for pos in reversed(inserts):
        src = src[:pos] + " long" + src[pos:]
    return src, bool(inserts)


# --------------------------------------------------------------------------- #
#  Compiling and running
# --------------------------------------------------------------------------- #

RUNTIME_C = r"""
#include <stdio.h>
#ifdef _WIN32
# include <io.h>
# include <fcntl.h>
/* no wildcard expansion of argv (Linux shells would not do it inside quotes) */
int _dowildcard = 0;
#endif

__attribute__((constructor))
static void examshell_runtime_init(void)
{
#ifdef _WIN32
	/* no "\n" -> "\r\n" translation: output must match byte for byte */
	_setmode(0, _O_BINARY);
	_setmode(1, _O_BINARY);
	_setmode(2, _O_BINARY);
#endif
	/* keep partial output if the program crashes */
	setvbuf(stdout, NULL, _IONBF, 0);
}
"""

WINDOWS_CRASH_CODES = {
    0xC0000005: "Segmentation fault (access violation)",
    0xC00000FD: "Stack overflow (infinite recursion?)",
    0xC0000094: "Division by zero",
    0xC0000095: "Integer overflow",
    0xC000001D: "Illegal instruction",
    0xC0000374: "Heap corruption (double free / invalid free / buffer overflow?)",
    0xC0000409: "Abort / stack buffer overrun",
    0xC0000417: "Invalid parameter passed to a C library function",
    0xC0000008: "Invalid handle",
    0x80000003: "Breakpoint / abort",
}


def describe_crash(returncode: int):
    if returncode is None:
        return None
    if IS_WINDOWS:
        code = returncode & 0xFFFFFFFF
        if code >= 0xC0000000 or code == 0x80000003:
            return WINDOWS_CRASH_CODES.get(code, f"Crash (exception 0x{code:08X})")
        return None
    if returncode < 0:
        import signal
        try:
            name = signal.Signals(-returncode).name
        except ValueError:
            name = f"signal {-returncode}"
        return {"SIGSEGV": "Segmentation fault", "SIGBUS": "Bus error",
                "SIGABRT": "Abort"}.get(name, name)
    return None


def find_compiler():
    env = os.environ.get("EXAMSHELL_CC")
    if env:
        return env
    for name in ("gcc", "cc", "clang"):
        path = shutil.which(name)
        if path:
            return path
    if IS_WINDOWS:
        candidates = [Path(p) for p in (r"C:\msys64\ucrt64\bin\gcc.exe", r"C:\msys64\mingw64\bin\gcc.exe",
                                        r"C:\MinGW\bin\gcc.exe", r"C:\TDM-GCC-64\bin\gcc.exe")]
        winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            candidates += list(winget.glob("*WinLibs*/mingw64/bin/gcc.exe"))
        for cand in candidates:
            if cand.is_file():
                return str(cand)
    return None


def _subprocess_env(cc: str) -> dict:
    env = dict(os.environ)
    cc_dir = os.path.dirname(cc)
    if cc_dir:
        env["PATH"] = cc_dir + os.pathsep + env.get("PATH", "")
    return env


def run_binary(exe: Path, args: list, cwd: Path, env: dict):
    """Returns (stdout_bytes, returncode or None, timed_out)."""
    try:
        proc = subprocess.run([str(exe)] + list(args), cwd=str(cwd), env=env,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=RUN_TIMEOUT)
        return proc.stdout, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        return exc.stdout or b"", None, True


class Toolchain:
    def __init__(self, cc: str):
        self.cc = cc
        self.env = _subprocess_env(cc)
        self._runtime_obj = None

    def describe(self) -> str:
        try:
            out = subprocess.run([self.cc, "-dumpfullversion"], env=self.env, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=10).stdout.decode().strip()
        except (OSError, subprocess.SubprocessError):
            out = ""
        return f"{Path(self.cc).stem.lower()} {out}".strip()

    def _run_cc(self, args: list, cwd: Path):
        proc = subprocess.run([self.cc] + args, cwd=str(cwd), env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.returncode == 0, proc.stdout.decode("utf-8", "replace")

    def runtime_obj(self) -> Path:
        if self._runtime_obj is None or not self._runtime_obj.exists():
            rt_dir = BUILD_DIR / "runtime"
            rt_dir.mkdir(parents=True, exist_ok=True)
            (rt_dir / "examshell_runtime.c").write_text(RUNTIME_C, encoding="utf-8")
            ok, out = self._run_cc(["-c", "examshell_runtime.c", "-o", "examshell_runtime.o"], rt_dir)
            if not ok:
                raise RuntimeError("could not compile the examshell runtime helper:\n" + out)
            self._runtime_obj = rt_dir / "examshell_runtime.o"
        return self._runtime_obj

    def build(self, build_dir: Path, c_files: list, output: str, extra_flags=()):
        cmd = CFLAGS + list(extra_flags) + ["-I", "."] + list(c_files) + \
            [str(self.runtime_obj()), "-o", output] + LDFLAGS
        ok, out = self._run_cc(cmd, build_dir)
        shown = " ".join(["gcc"] + CFLAGS + list(extra_flags) + list(c_files) + ["-o", output])
        return ok, out, shown


# --------------------------------------------------------------------------- #
#  Grading
# --------------------------------------------------------------------------- #

@dataclass
class GradeResult:
    passed: bool
    reason: str
    details: str
    trace: str


def cat_e(data: bytes) -> str:
    out = []
    for byte in data:
        ch = chr(byte)
        if ch == "\n":
            out.append("$\n")
        elif ch == "\t":
            out.append("^I")
        elif byte < 32:
            out.append("^" + chr(byte + 64))
        elif byte == 127:
            out.append("^?")
        elif byte > 127:
            out.append(f"\\x{byte:02x}")
        else:
            out.append(ch)
    return "".join(out)


def quote_arg(arg: str) -> str:
    if "\t" in arg or "\n" in arg:
        inner = arg.replace("\\", "\\\\").replace("'", "\\'").replace("\t", "\\t").replace("\n", "\\n")
        return f"$'{inner}'"
    return '"' + arg.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _clip(line: str, width: int = 160) -> str:
    return line if len(line) <= width else line[:width] + f"{C.DIM}... (+{len(line) - width} chars){C.RESET}"


def describe_mismatch(expected: bytes, got: bytes, full: bool):
    """Returns (console_text, trace_text)."""
    exp_lines = cat_e(expected).split("\n")
    got_lines = cat_e(got).split("\n")
    idx = 0
    while idx < len(exp_lines) and idx < len(got_lines) and exp_lines[idx] == got_lines[idx]:
        idx += 1
    def pick(lines: list) -> str:
        if idx >= len(lines) or (idx == len(lines) - 1 and lines[idx] == ""):
            return "<no more output>"
        return lines[idx]

    exp_line, got_line = pick(exp_lines), pick(got_lines)
    trace = ("expected output (cat -e):\n" + cat_e(expected) +
             "\n\nyour output (cat -e):\n" + cat_e(got) +
             f"\n\nfirst difference at line {idx + 1}:\n  expected: {exp_line}\n  yours   : {got_line}\n")
    if full and len(exp_lines) <= 12 and len(got_lines) <= 12:
        console = (f"  expected: {_clip(cat_e(expected).rstrip(chr(10)).replace(chr(10), chr(10) + '            '))}\n"
                   f"  yours   : {_clip(cat_e(got).rstrip(chr(10)).replace(chr(10), chr(10) + '            ')) or '<nothing>'}")
    else:
        console = (f"  first difference at output line {idx + 1}:\n"
                   f"  expected: {_clip(exp_line)}\n"
                   f"  yours   : {_clip(got_line)}")
    return console, trace


def collect_student_files(ex: Exercise, rendu: Path):
    """Returns (files: dict name->Path, missing: list)."""
    if not rendu.is_dir():
        return {}, list(ex.expected_files)
    present = {p.name: p for p in rendu.iterdir() if p.is_file()}
    files, missing = {}, []
    for pattern in ex.expected_files:
        if "*" in pattern:
            suffix = pattern.replace("*", "")
            matched = {n: p for n, p in present.items() if n.endswith(suffix)}
            if not matched and suffix == ".c":
                missing.append(pattern)
            files.update(matched)
        elif pattern in present:
            files[pattern] = present[pattern]
        else:
            missing.append(pattern)
    return files, missing


def _hash_dir_files(paths: list) -> str:
    h = hashlib.sha1()
    for p in sorted(paths, key=lambda x: str(x)):
        h.update(str(p.name).encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def _link_hints(output: str, ex: Exercise) -> str:
    hints = []
    if "multiple definition of `main'" in output or "multiple definition of 'main'" in output:
        hints.append("Hint: remove your main() - the grader uses its own main for function exercises.")
    if ex.kind == "program" and ("WinMain" in output or "undefined reference to `main'" in output):
        hints.append("Hint: this is a program exercise, your file needs a main() function.")
    if ex.kind == "function" and "undefined reference to" in output:
        hints.append(f"Hint: check the name and prototype of the function the subject asks for.")
    return ("\n  " + "\n  ".join(hints)) if hints else ""


def grade(ex: Exercise, rendu: Path, tools: Toolchain, progress=None) -> GradeResult:
    trace = [f"= examshell trace: {ex.name} (level {ex.level}) =",
             f"date   : {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"folder : {rendu}", ""]

    def fail(reason: str, details: str, extra_trace: str = "") -> GradeResult:
        trace.append(f"RESULT: FAILURE - {reason}")
        trace.append(re.sub(r"\033\[[0-9;]*m", "", extra_trace or details))
        return GradeResult(False, reason, details, "\n".join(trace) + "\n")

    # 1. expected files ------------------------------------------------------
    files, missing = collect_student_files(ex, rendu)
    if missing:
        where = rendu if rendu.is_dir() else f"{rendu} (folder does not exist)"
        return fail("Missing file", f"  expected file(s) not found: {', '.join(missing)}\n  in: {where}")
    trace.append("files  : " + ", ".join(sorted(files)))

    # 2. forbidden functions -------------------------------------------------
    sources = {n: p.read_text(encoding="utf-8", errors="replace") for n, p in files.items()}
    forbidden = find_forbidden_calls(sources, ex.allowed_functions)
    if forbidden:
        allowed = ", ".join(ex.allowed_functions) if ex.allowed_functions else "none"
        lines = [f"  {C.BOLD}{name}{C.RESET} used in {f}:{line}" for name, f, line in forbidden]
        return fail("Forbidden function", "\n".join(lines) + f"\n  allowed functions: {allowed}")

    # 3. reference binary (cached) -------------------------------------------
    if progress:
        progress("compiling")
    ref_sources = list((ex.path / "ref").iterdir()) + [ex.path / "attach" / a for a in ex.attachments]
    if ex.kind == "function":
        ref_sources.append(ex.path / "tester" / "main.c")
    ref_dir = BUILD_DIR / "ref" / f"{ex.name}-{_hash_dir_files(ref_sources)}"
    ref_exe = ref_dir / f"ref{EXE_SUFFIX}"
    if not ref_exe.exists():
        shutil.rmtree(ref_dir, ignore_errors=True)
        ref_dir.mkdir(parents=True)
        for p in ref_sources:
            target = "examshell_main.c" if p.name == "main.c" and p.parent.name == "tester" else p.name
            shutil.copyfile(p, ref_dir / target)
        c_files = sorted(p.name for p in ref_dir.iterdir() if p.suffix == ".c")
        ok, out, _ = tools.build(ref_dir, c_files, f"ref{EXE_SUFFIX}")
        if not ok:
            raise RuntimeError(f"reference solution for {ex.name} does not compile:\n{out}")

    # 4. student binary ------------------------------------------------------
    user_dir = BUILD_DIR / "user" / f"{ex.name}-{int(time.time() * 1000)}"
    user_dir.mkdir(parents=True)
    extra_flags = []
    for name, src in sources.items():
        if IS_WINDOWS and (name.endswith(".c") or name.endswith(".h")):
            src, changed = widen_long(src)
            if changed:
                extra_flags = ["-Wno-format"]
        (user_dir / name).write_bytes(src.encode("utf-8", "surrogateescape"))
    for a in ex.attachments:
        shutil.copyfile(ex.path / "attach" / a, user_dir / a)
    c_files = sorted(n for n in files if n.endswith(".c"))
    if ex.kind == "function":
        shutil.copyfile(ex.path / "tester" / "main.c", user_dir / "examshell_main.c")
        c_files.append("examshell_main.c")
    user_exe = user_dir / f"user{EXE_SUFFIX}"
    ok, out, shown_cmd = tools.build(user_dir, c_files, f"user{EXE_SUFFIX}", extra_flags)
    trace.append(f"compile: {shown_cmd}")
    if not ok:
        out = out.replace("examshell_main.c", "<grader main.c>")
        out = re.sub(r"\S*[\\/]ld(\.exe)?:", "ld:", out)
        out = re.sub(r"[A-Za-z]:[\\/]\S*?[\\/]cc\w+\.o:", "", out)
        return fail("Compilation error", "  " + "\n  ".join(out.strip().splitlines()[:25]) + _link_hints(out, ex),
                    out + _link_hints(out, ex))

    # 5. tests ---------------------------------------------------------------
    if ex.kind == "program":
        rng = random.Random()
        gen = GENERATORS.get(ex.generator)
        tests = [list(t) for t in ex.fixed_tests]
        if gen:
            tests += [gen(rng) for _ in range(ex.random_tests)]
        labels = [" ".join([f"./{ex.name}"] + [quote_arg(a) for a in t]) for t in tests]
    else:
        tests = [[str(seed)] for seed in range(ex.seeds + 1)]
        labels = ["fixed edge cases" if seed == 0 else f"random tests, seed {seed}"
                  for seed in range(ex.seeds + 1)]
    trace.append("")
    for i, (args, label) in enumerate(zip(tests, labels), 1):
        if progress:
            progress(f"test {i}/{len(tests)}")
        header = f"Test {i}/{len(tests)}: {label}"
        expected, ref_rc, ref_to = run_binary(ref_exe, args, ref_dir, tools.env)
        if ref_to or describe_crash(ref_rc):
            raise RuntimeError(f"reference binary misbehaved on {label}")
        got, rc, timed_out = run_binary(user_exe, args, user_dir, tools.env)
        if timed_out:
            console, full = describe_mismatch(expected, got, ex.kind == "program")
            return fail("Timeout", f"  {header}\n  your code ran for more than {RUN_TIMEOUT}s (infinite loop?)",
                        f"{header}\nTIMEOUT after {RUN_TIMEOUT}s\n\n{full}")
        crash = describe_crash(rc)
        if crash:
            console, full = describe_mismatch(expected, got, ex.kind == "program")
            return fail("Crash", f"  {header}\n  {C.RED}{crash}{C.RESET}\n{console}",
                        f"{header}\nCRASH: {crash}\n\n{full}")
        if got != expected:
            console, full = describe_mismatch(expected, got, ex.kind == "program")
            return fail("Wrong output", f"  {header}\n{console}", f"{header}\n\n{full}")
        trace.append(f"[OK] {header}")
    trace.append("")
    trace.append(f"RESULT: SUCCESS - all {len(tests)} tests passed")
    return GradeResult(True, "Success", f"  all {len(tests)} tests passed", "\n".join(trace) + "\n")


def print_grade_result(result: GradeResult, trace_path=None) -> None:
    print()
    if result.passed:
        print(f"{C.GREEN}{C.BOLD}>>>>>>>>>>>>>>>>>>>>>>>>>>>> SUCCESS <<<<<<<<<<<<<<<<<<<<<<<<<<<<{C.RESET}")
    else:
        print(f"{C.RED}{C.BOLD}>>>>>>>>>>>>>>>>>>>>>>>>>>>> FAILURE <<<<<<<<<<<<<<<<<<<<<<<<<<<<{C.RESET}")
        print(f"  {C.BOLD}{result.reason}{C.RESET}")
    print(result.details)
    if trace_path:
        print(f"  {C.DIM}trace: {trace_path}{C.RESET}")
    print()


# --------------------------------------------------------------------------- #
#  Workspaces and shells
# --------------------------------------------------------------------------- #

class Workspace:
    """subjects/ rendu/ traces/ - the same layout as on the exam machines."""

    def __init__(self, root: Path):
        self.root = root
        self.subjects = root / "subjects"
        self.rendu_root = root / "rendu"
        self.traces = root / "traces"

    def rendu(self, ex: Exercise) -> Path:
        return self.rendu_root / ex.name

    def subject_file(self, ex: Exercise) -> Path:
        return self.subjects / ex.name / "subject.en.txt"

    def setup(self, ex: Exercise) -> None:
        sub = self.subjects / ex.name
        sub.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ex.path / "subject.en.txt", sub / "subject.en.txt")
        for a in ex.attachments:
            shutil.copyfile(ex.path / "attach" / a, sub / a)
        self.rendu(ex).mkdir(parents=True, exist_ok=True)
        self.traces.mkdir(parents=True, exist_ok=True)

    def new_trace_path(self, ex: Exercise) -> Path:
        self.traces.mkdir(parents=True, exist_ok=True)
        n = len(list(self.traces.glob("*.trace"))) + 1
        return self.traces / f"{n:02d}-{ex.name}.trace"


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if IS_WINDOWS:
        os.startfile(str(path))
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


class Shell:
    mode = ""

    def __init__(self, tools: Toolchain, exercises: list, workspace: Workspace):
        self.tools = tools
        self.exercises = exercises
        self.by_name = {e.name: e for e in exercises}
        self.ws = workspace
        self.current = None
        self.running = True

    # -- overridable ---------------------------------------------------------
    def extra_commands(self) -> dict:
        return {}

    def extra_help(self) -> list:
        return []

    def before_command(self) -> bool:
        return True

    def after_grade(self, result: GradeResult) -> None:
        pass

    def status_lines(self) -> list:
        return []

    def prompt(self) -> str:
        return f"{C.CYAN}{C.BOLD}examshell{C.RESET}> "

    # -- loop ------------------------------------------------------------------
    def commands(self) -> dict:
        cmds = {
            "help": self.cmd_help, "?": self.cmd_help,
            "status": self.cmd_status,
            "subject": self.cmd_subject,
            "grademe": self.cmd_grademe,
            "open": self.cmd_open,
            "code": self.cmd_code,
            "clear": self.cmd_clear, "cls": self.cmd_clear,
            "exit": self.cmd_exit, "quit": self.cmd_exit, "menu": self.cmd_exit,
        }
        cmds.update(self.extra_commands())
        return cmds

    def loop(self) -> None:
        while self.running:
            try:
                line = input(self.prompt())
            except EOFError:
                print()
                return
            except KeyboardInterrupt:
                print()
                continue
            parts = line.split()
            if not parts:
                continue
            handler = self.commands().get(parts[0].lower())
            if handler is None:
                print(f"  unknown command '{parts[0]}' - type {C.BOLD}help{C.RESET}")
                continue
            if not self.before_command():
                continue
            try:
                handler(parts[1:])
            except KeyboardInterrupt:
                print(f"\n  {C.YELLOW}interrupted{C.RESET}")

    # -- commands --------------------------------------------------------------
    def cmd_help(self, args: list) -> None:
        print()
        rows = [("grademe", "grade your current assignment"),
                ("status", "show assignment, folders and time"),
                ("subject", "print the subject"),
                ("open", "open your rendu folder in Explorer"),
                ("code", "open your rendu folder in VS Code"),
                ("clear", "clear the screen")] + self.extra_help() + \
               [("exit", "back to the main menu")]
        for name, desc in rows:
            print(f"  {C.BOLD}{name:<16}{C.RESET}{desc}")
        print()

    def cmd_status(self, args: list) -> None:
        print()
        rule(f"{self.mode} mode")
        if self.current:
            ex = self.current
            print(f"  {'assignment':<12}: {C.BOLD}{C.YELLOW}{ex.name}{C.RESET}  (level {ex.level}, {ex.kind})")
            print(f"  {'files':<12}: {', '.join(ex.expected_files)}")
            allowed = ", ".join(ex.allowed_functions) if ex.allowed_functions else "none"
            print(f"  {'allowed':<12}: {allowed}")
            print(f"  {'subject':<12}: {self.ws.subject_file(ex)}")
            print(f"  {'your code':<12}: {C.BOLD}{self.ws.rendu(ex)}{os.sep}{C.RESET}")
        else:
            print("  no assignment selected")
        for line in self.status_lines():
            print(f"  {line}")
        rule()
        print()

    def cmd_subject(self, args: list) -> None:
        if not self.current:
            print("  no assignment selected")
            return
        print()
        rule(f"subject: {self.current.name}")
        print(self.current.subject.rstrip())
        rule()
        attach = self.current.attachments
        if attach:
            print(f"  provided file(s) in {self.ws.subjects / self.current.name}: {', '.join(attach)}")
        print(f"  put your files in: {C.BOLD}{self.ws.rendu(self.current)}{os.sep}{C.RESET}")
        print()

    def cmd_grademe(self, args: list) -> None:
        if not self.current:
            print("  no assignment selected")
            return
        ex = self.current

        def progress(msg: str) -> None:
            sys.stdout.write(f"\r  {C.DIM}grading {ex.name}: {msg:<24}{C.RESET}")
            sys.stdout.flush()

        try:
            result = grade(ex, self.ws.rendu(ex), self.tools, progress)
        except KeyboardInterrupt:
            print(f"\n  {C.YELLOW}grading cancelled{C.RESET}")
            return
        except RuntimeError as err:
            print(f"\n  {C.RED}internal grader error:{C.RESET} {err}")
            return
        sys.stdout.write("\r" + " " * 60 + "\r")
        trace_path = self.ws.new_trace_path(ex)
        trace_path.write_text(result.trace, encoding="utf-8")
        print_grade_result(result, trace_path)
        self.after_grade(result)

    def cmd_open(self, args: list) -> None:
        if self.current:
            open_folder(self.ws.rendu(self.current))
            print(f"  opened {self.ws.rendu(self.current)}")

    def cmd_code(self, args: list) -> None:
        if not self.current:
            return
        code = shutil.which("code")
        if not code:
            print("  VS Code ('code') is not on your PATH - use 'open' instead")
            return
        rendu = self.ws.rendu(self.current)
        rendu.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(f'"{code}" "{rendu}"', shell=True)
        print(f"  opening {rendu} in VS Code")

    def cmd_clear(self, args: list) -> None:
        clear_screen()

    def cmd_exit(self, args: list) -> None:
        self.running = False


class ExamShell(Shell):
    mode = "exam"
    STATE_FILE = EXAM_DIR / "current.json"

    def __init__(self, tools: Toolchain, exercises: list, state: dict):
        super().__init__(tools, exercises, Workspace(ROOT / state["session"]))
        state.setdefault("levels", [4])          # exams started by older versions
        state.setdefault("level_index", 0)
        self.state = state
        self.current = self.by_name.get(state["current"])

    # -- state -------------------------------------------------------------------
    @classmethod
    def load_state(cls):
        try:
            state = json.loads(cls.STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return None if state.get("finished") else state

    def save(self) -> None:
        EXAM_DIR.mkdir(parents=True, exist_ok=True)
        self.STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    @classmethod
    def new(cls, tools: Toolchain, exercises: list, minutes: int, levels: list) -> "ExamShell":
        session = f"exam/{time.strftime('%Y-%m-%d_%H-%M-%S')}"
        state = {"session": session, "start": time.time(), "minutes": minutes, "current": None,
                 "levels": levels, "level_index": 0, "seen": [], "history": [],
                 "finished": False, "passed": False}
        shell = cls(tools, exercises, state)
        shell.assign_random()
        return shell

    @property
    def level(self) -> int:
        levels = self.state["levels"]
        return levels[min(self.state["level_index"], len(levels) - 1)]

    @property
    def full_exam(self) -> bool:
        return len(self.state["levels"]) > 1

    def score(self) -> str:
        done, total = self.state["level_index"], len(self.state["levels"])
        return f"{done * 100 // total}/100"

    def remaining(self) -> float:
        return self.state["start"] + self.state["minutes"] * 60 - time.time()

    def assign_random(self) -> None:
        level_pool = [e for e in self.exercises if e.level == self.level] or self.exercises
        pool = [e for e in level_pool if e.name not in self.state["seen"]]
        if not pool:  # every exercise of this level was seen: allow repeats, but not the same one twice in a row
            pool = [e for e in level_pool if e.name != self.state["current"]] or level_pool
        ex = random.choice(pool)
        self.state["seen"].append(ex.name)
        self.state["current"] = ex.name
        self.current = ex
        self.ws.setup(ex)
        self.save()

    def finish(self, passed: bool, why: str) -> None:
        self.state["finished"] = True
        self.state["passed"] = passed
        self.save()
        EXAM_DIR.mkdir(parents=True, exist_ok=True)
        used = self.state["minutes"] * 60 - max(0, self.remaining())
        levels = "levels " + "-".join(str(lv) for lv in self.state["levels"])
        with open(EXAM_DIR / "history.log", "a", encoding="utf-8") as log:
            tries = ", ".join(f"{h['exercise']}:{'OK' if h['passed'] else 'KO'}" for h in self.state["history"])
            log.write(f"{time.strftime('%Y-%m-%d %H:%M')}  {'PASSED' if passed else 'FAILED'}  {self.score()}  "
                      f"{levels}  time {fmt_duration(used)}  [{tries}]  ({why})\n")
        self.running = False

    # -- shell hooks ---------------------------------------------------------------
    def prompt(self) -> str:
        left = self.remaining()
        color = C.GREEN if left > 15 * 60 else C.YELLOW if left > 5 * 60 else C.RED
        return (f"{color}[{fmt_duration(left)}]{C.RESET} {C.MAGENTA}L{self.level}{C.RESET} "
                f"{C.CYAN}{C.BOLD}examshell{C.RESET}> ")

    def before_command(self) -> bool:
        if self.remaining() <= 0:
            print(f"\n  {C.RED}{C.BOLD}Time is up!{C.RESET} The exam is over. Final score: {self.score()}\n")
            self.finish(False, "time is up")
            return False
        return True

    def extra_commands(self) -> dict:
        return {"finish": self.cmd_finish}

    def extra_help(self) -> list:
        return [("finish", "give up and end the exam")]

    def status_lines(self) -> list:
        fails = sum(1 for h in self.state["history"] if not h["passed"])
        levels = self.state["levels"]
        lines = [f"{'time left':<12}: {fmt_duration(self.remaining())}"]
        if self.full_exam:
            lines.append(f"{'level':<12}: {self.level}   (levels {levels[0]} -> {levels[-1]}, score {self.score()})")
        lines += [f"{'failed tries':<12}: {fails}", f"{'session':<12}: {self.ws.root}"]
        return lines

    def after_grade(self, result: GradeResult) -> None:
        self.state["history"].append({"exercise": self.current.name, "level": self.level,
                                      "passed": result.passed, "at": time.time(), "reason": result.reason})
        self.save()
        fails = sum(1 for h in self.state["history"] if not h["passed"])
        if result.passed:
            finished_level = self.level
            self.state["level_index"] += 1
            if self.state["level_index"] >= len(self.state["levels"]):
                used = self.state["minutes"] * 60 - self.remaining()
                what = "Exam Rank 02 passed - 100/100!" if self.full_exam else \
                    f"Level {finished_level} validated - exam passed!"
                print(f"  {C.GREEN}{C.BOLD}{what}{C.RESET}  (time used: {fmt_duration(used)}, "
                      f"failed tries: {fails})\n")
                self.finish(True, "passed")
                ask("  press Enter to go back to the menu ")
                return
            self.assign_random()
            print(f"  {C.GREEN}{C.BOLD}Level {finished_level} validated!{C.RESET}  score: {self.score()}")
            print(f"  Level {self.level} - your new assignment: {C.BOLD}{C.YELLOW}{self.current.name}{C.RESET}")
        else:
            tries = sum(1 for h in self.state["history"] if h["exercise"] == self.current.name and not h["passed"])
            print(f"  {C.YELLOW}Not yet ({tries} failed tr{'y' if tries == 1 else 'ies'} on {self.current.name}).{C.RESET} "
                  f"Read the trace above, fix your code and type {C.BOLD}grademe{C.RESET} again - "
                  f"you can retry as often as you want.\n")
            return
        print(f"  subject  : {self.ws.subject_file(self.current)}")
        print(f"  your code: {self.ws.rendu(self.current)}{os.sep}\n")

    def cmd_finish(self, args: list) -> None:
        if confirm("  Really end the exam now?"):
            self.finish(False, "gave up")
            print(f"  exam finished - score {self.score()}\n")

    def cmd_exit(self, args: list) -> None:
        print(f"  {C.DIM}the exam keeps running - you can resume it from the menu{C.RESET}")
        self.running = False

    def start(self) -> None:
        levels = self.state["levels"]
        print()
        rule("exam")
        if self.full_exam:
            print(f"  Exam       : Exam Rank 02, levels {levels[0]} -> {levels[-1]}   (score {self.score()})")
        print(f"  Level      : {self.level}")
        print(f"  Assignment : {C.BOLD}{C.YELLOW}{self.current.name}{C.RESET}")
        print(f"  Time left  : {fmt_duration(self.remaining())}")
        print(f"  Subject    : {self.ws.subject_file(self.current)}")
        print(f"  Your code  : {C.BOLD}{self.ws.rendu(self.current)}{os.sep}{C.RESET}")
        print()
        print("  Write your solution in the rendu folder, then type 'grademe'.")
        if self.full_exam:
            print("  Pass = next level. Fail = you see the trace and retry, as often as you want.")
        else:
            print("  Fail = you see the trace and retry, as often as you want. Pass = exam passed.")
        rule()
        print(f"  type {C.BOLD}subject{C.RESET} to read it, {C.BOLD}help{C.RESET} for all commands\n")
        self.loop()


class PracticeShell(Shell):
    mode = "practice"
    PROGRESS_FILE = PRACTICE_DIR / "progress.json"

    def __init__(self, tools: Toolchain, exercises: list):
        super().__init__(tools, exercises, Workspace(PRACTICE_DIR))
        try:
            self.progress = json.loads(self.PROGRESS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.progress = {}
        self.progress.setdefault("passed", {})
        self.progress.setdefault("attempts", {})
        last = self.by_name.get(self.progress.get("current", ""))
        if last:
            self.select(last, quiet=True)

    def save(self) -> None:
        PRACTICE_DIR.mkdir(parents=True, exist_ok=True)
        self.PROGRESS_FILE.write_text(json.dumps(self.progress, indent=2), encoding="utf-8")

    def select(self, ex: Exercise, quiet: bool = False) -> None:
        self.current = ex
        self.ws.setup(ex)
        self.progress["current"] = ex.name
        self.save()
        if not quiet:
            print(f"\n  assignment: {C.BOLD}{C.YELLOW}{ex.name}{C.RESET}")
            print(f"  subject   : {self.ws.subject_file(ex)}")
            print(f"  your code : {C.BOLD}{self.ws.rendu(ex)}{os.sep}{C.RESET}\n")

    def extra_commands(self) -> dict:
        return {"list": self.cmd_list, "ls": self.cmd_list, "pick": self.cmd_pick,
                "select": self.cmd_pick, "next": self.cmd_next, "random": self.cmd_next,
                "reset": self.cmd_reset, "learn": self.cmd_learn, "bugs": self.cmd_bugs,
                "predict": self.cmd_predict}

    def extra_help(self) -> list:
        return [("list", "list all exercises and your progress"),
                ("pick <name|#>", "switch to an exercise"),
                ("list [level]", "only show one level"),
                ("next [level]", "random exercise you have not passed yet"),
                ("learn", "fill-the-gap lesson for this exercise"),
                ("bugs", "find-the-bug puzzles for this exercise"),
                ("predict", "predict-the-output quiz for this exercise"),
                ("reset", "forget your practice progress")]

    def status_lines(self) -> list:
        return [f"{'progress':<12}: {len(self.passed_names())}/{len(self.exercises)} passed"]

    def passed_names(self) -> set:
        return set(self.progress["passed"]) & set(self.by_name)

    def _level_arg(self, args: list):
        if args and args[0].isdigit() and any(e.level == int(args[0]) for e in self.exercises):
            return int(args[0])
        return None

    def cmd_list(self, args: list) -> None:
        only = self._level_arg(args)
        print()
        print(f"  {C.DIM}{'#':>3}  {'exercise':<20}{'type':<10}{'allowed functions':<30}status{C.RESET}")
        last_level = None
        for i, ex in enumerate(self.exercises, 1):
            if only is not None and ex.level != only:
                continue
            if ex.level != last_level:
                last_level = ex.level
                in_level = [e for e in self.exercises if e.level == ex.level]
                done = sum(1 for e in in_level if e.name in self.progress["passed"])
                print(f"  {C.MAGENTA}{C.BOLD}level {ex.level}{C.RESET} {C.DIM}({done}/{len(in_level)} passed){C.RESET}")
            tries = self.progress["attempts"].get(ex.name, 0)
            if ex.name in self.progress["passed"]:
                status = f"{C.GREEN}PASSED{C.RESET} {C.DIM}({tries} tr{'y' if tries == 1 else 'ies'}){C.RESET}"
            elif tries:
                status = f"{C.RED}not yet{C.RESET} {C.DIM}({tries} tr{'y' if tries == 1 else 'ies'}){C.RESET}"
            else:
                status = f"{C.DIM}-{C.RESET}"
            marker = f"{C.YELLOW}>{C.RESET}" if ex is self.current else " "
            allowed = ", ".join(ex.allowed_functions) or "none"
            print(f" {marker}{i:>3}  {ex.name:<20}{ex.kind:<10}{allowed:<30}{status}")
        print(f"\n  {len(self.passed_names())}/{len(self.exercises)} passed - "
              f"{C.BOLD}pick <name|#>{C.RESET}, {C.BOLD}next [level]{C.RESET}, {C.BOLD}list <level>{C.RESET}\n")

    def print_overview(self) -> None:
        for level in sorted({e.level for e in self.exercises}):
            in_level = [e for e in self.exercises if e.level == level]
            done = sum(1 for e in in_level if e.name in self.progress["passed"])
            bar = "#" * done + "." * (len(in_level) - done)
            color = C.GREEN if done == len(in_level) else C.YELLOW if done else C.DIM
            print(f"  level {level}  {color}{bar}{C.RESET}  {done}/{len(in_level)} passed")
        print()

    def cmd_pick(self, args: list) -> None:
        if not args:
            self.cmd_list([])
            return
        key = args[0].lower()
        ex = None
        if key.isdigit() and 1 <= int(key) <= len(self.exercises):
            ex = self.exercises[int(key) - 1]
        else:
            matches = [e for e in self.exercises if e.name == key] or \
                      [e for e in self.exercises if e.name.startswith(key)]
            if len(matches) == 1:
                ex = matches[0]
        if not ex:
            print(f"  no (unique) exercise matches '{args[0]}' - type 'list'")
            return
        self.select(ex)

    def cmd_next(self, args: list) -> None:
        only = self._level_arg(args)
        candidates = [e for e in self.exercises if only is None or e.level == only]
        pool = [e for e in candidates if e.name not in self.progress["passed"] and e is not self.current]
        if not pool:
            if all(e.name in self.progress["passed"] for e in candidates):
                where = f"of level {only}" if only is not None else ""
                print(f"\n  {C.GREEN}{C.BOLD}You passed every exercise {where}!{C.RESET} "
                      f"Picking a random one to redo.")
            pool = [e for e in candidates if e is not self.current] or candidates
        self.select(random.choice(pool))

    def cmd_learn(self, args: list) -> None:
        lesson = load_lesson(self.current) if self.current else None
        if not lesson or not lesson.order:
            print("  no fill-the-gap lesson for this exercise")
            return
        results = run_lesson(self.current, lesson)
        if results is not None:
            record_lesson_result(self.current, lesson, results)
        print(f"\n  {C.DIM}back in practice mode - now write {self.current.name} yourself in "
              f"{self.ws.rendu(self.current)}{os.sep}{C.RESET}\n")

    def cmd_bugs(self, args: list) -> None:
        if self.current:
            play_exercise_bugs(self.tools, self.current)
            print(f"\n  {C.DIM}back in practice mode ({self.current.name}){C.RESET}\n")

    def cmd_predict(self, args: list) -> None:
        if self.current:
            play_exercise_quiz(self.current)
            print(f"\n  {C.DIM}back in practice mode ({self.current.name}){C.RESET}\n")

    def cmd_reset(self, args: list) -> None:
        if confirm("  Forget all practice progress? (your code in practice/rendu stays)"):
            self.progress = {"passed": {}, "attempts": {}, "current": self.current.name if self.current else ""}
            self.save()
            print("  progress reset")

    def after_grade(self, result: GradeResult) -> None:
        name = self.current.name
        self.progress["attempts"][name] = self.progress["attempts"].get(name, 0) + 1
        if result.passed:
            self.progress["passed"].setdefault(name, time.strftime("%Y-%m-%d %H:%M"))
            left = len(self.exercises) - len(self.passed_names())
            msg = "all exercises passed!" if left == 0 else f"{left} exercise(s) left - type 'next'"
            print(f"  {C.GREEN}{name} passed{C.RESET} - {msg}\n")
        self.save()

    def start(self) -> None:
        print()
        rule("practice")
        print("  Pick any exercise and retry as often as you like.")
        print(f"  Your code goes in {C.BOLD}{PRACTICE_DIR / 'rendu'}{os.sep}<exercise>{os.sep}{C.RESET}")
        rule()
        print()
        self.print_overview()
        print(f"  {C.BOLD}list{C.RESET} shows every exercise, {C.BOLD}list 2{C.RESET} only level 2, "
              f"{C.BOLD}next 3{C.RESET} picks a random level-3 exercise\n")
        if self.current:
            print(f"  current assignment: {C.BOLD}{C.YELLOW}{self.current.name}{C.RESET} "
                  f"({self.ws.rendu(self.current)}{os.sep})\n")
        self.loop()


# --------------------------------------------------------------------------- #
#  Fill the gap
# --------------------------------------------------------------------------- #

GAP_MARK_RE = re.compile(r"\{\{(\d+)\}\}")
ANSWER_TOKEN_RE = re.compile(
    r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|[A-Za-z_]\w*|\d+|->|\+\+|--|<<=|>>=|<<|>>"
    r"|<=|>=|==|!=|&&|\|\||[-+*/%&|^]=|\S")
GAP_PROGRESS_FILE = PRACTICE_DIR / "fill_the_gap.json"


@dataclass
class Gap:
    number: int
    answer: str
    accept: list
    wrong: list          # [(answer, feedback)]
    hint: str
    explanation: str


@dataclass
class Lesson:
    intro: str
    files: list          # [(file name, code containing {{n}} markers)]
    gaps: dict           # number -> Gap
    order: list          # gap numbers in order of appearance
    outro: str


def load_lesson(ex: Exercise):
    """Parse exercises/<level>/<name>/gaps.txt (sections: @@ intro, @@ file <name>,
    @@ gap <n> with answer:/accept:/wrong:/hint: lines, @@ outro)."""
    path = ex.path / "gaps.txt"
    if not path.is_file():
        return None
    sections = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("@@ "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    lesson = Lesson("", [], {}, [], "")
    for header, lines in sections:
        body = "\n".join(lines).strip("\n")
        if header == "intro":
            lesson.intro = body
        elif header == "outro":
            lesson.outro = body
        elif header.startswith("file "):
            lesson.files.append((header[5:].strip(), body))
        elif header.startswith("gap "):
            gap = Gap(int(header[4:]), "", [], [], "", "")
            k = 0
            while k < len(lines) and re.match(r"(answer|accept|wrong|hint):", lines[k]):
                key, _, value = lines[k].partition(":")
                value = value.strip()
                if key == "answer":
                    gap.answer = value
                elif key == "accept":
                    gap.accept.append(value)
                elif key == "hint":
                    gap.hint = value
                else:
                    wrong, _, feedback = value.partition(" => ")
                    gap.wrong.append((wrong.strip(), feedback.strip()))
                k += 1
            gap.explanation = "\n".join(lines[k:]).strip("\n")
            lesson.gaps[gap.number] = gap
    lesson.order = [int(m.group(1)) for _, code in lesson.files for m in GAP_MARK_RE.finditer(code)]
    return lesson


def answer_tokens(text: str) -> list:
    """Compare answers token by token, so spacing doesn't matter."""
    tokens = ANSWER_TOKEN_RE.findall(text.strip())
    while tokens and tokens[-1] == ";":
        tokens.pop()
    return tokens


def _term_width() -> int:
    return max(50, min(shutil.get_terminal_size((100, 24)).columns, 100))


def _colorize_backticks(lines: list) -> list:
    """`code` spans => cyan. Backticks stay visible when colors are off."""
    if not C.CYAN:
        return lines
    out, inside = [], False
    for line in lines:
        parts = line.split("`")
        buf = C.CYAN if inside else ""
        for idx, part in enumerate(parts):
            if idx:
                inside = not inside
                buf += C.CYAN if inside else C.RESET
            buf += part
        out.append(buf + (C.RESET if inside else ""))
    return out


def print_text(text: str, indent: int = 2) -> None:
    """Tiny markup: paragraphs are wrapped, lines indented by 4 are code,
    '- ' / '1. ' start list items, `backticks` are highlighted."""
    width = _term_width() - indent - 2
    pad = " " * indent
    para, hang = [], ""

    def flush():
        nonlocal para, hang
        if para:
            # keep `code spans` on one line: protect their spaces while wrapping
            joined = re.sub(r"`[^`]*`", lambda m: m.group().replace(" ", "\x00"), " ".join(para))
            joined = joined.replace(" - ", "\x00- ")  # a wrapped line must not start like a list item
            wrapped = textwrap.wrap(joined, width, subsequent_indent=hang,
                                    break_long_words=False, break_on_hyphens=False)
            for line in _colorize_backticks([w.replace("\x00", " ") for w in wrapped]):
                print(pad + line)
        para, hang = [], ""

    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line:
            flush()
            print()
        elif raw.startswith("    ") or raw.startswith("\t"):
            flush()
            print(f"{pad}{C.CYAN}{line.expandtabs(4)}{C.RESET}")
        elif re.match(r"(- |\d+\. )", line):
            flush()
            para, hang = [line], " " * len(re.match(r"(- |\d+\. )", line).group(1))
        elif hang and re.match(r" {2,3}\S", raw):
            para.append(line.strip())
        else:
            if hang:
                flush()
            para.append(line.strip())
    flush()


def print_feedback(label: str, color: str, text: str) -> None:
    width = _term_width() - 4
    lines = textwrap.wrap(f"{label} {text}".strip(), width, subsequent_indent="  ",
                          break_long_words=False, break_on_hyphens=False) or [label]
    lines = _colorize_backticks(lines)
    lines[0] = lines[0].replace(label, f"{color}{C.BOLD}{label}{C.RESET}", 1)
    for line in lines:
        print("  " + line)


def _render_code_line(line: str, fill) -> str:
    """Expand tabs (width 4) and replace {{n}} markers, keeping columns aligned."""
    out, col, pos = [], 0, 0
    for m in list(GAP_MARK_RE.finditer(line)) + [None]:
        for ch in (line[pos:m.start()] if m else line[pos:]):
            if ch == "\t":
                out.append(" " * (4 - col % 4))
                col += 4 - col % 4
            else:
                out.append(ch)
                col += 1
        if m is None:
            break
        visible, colored = fill(int(m.group(1)))
        out.append(colored)
        col += len(visible)
        pos = m.end()
    return "".join(out)


def print_lesson_code(lesson: Lesson, results: dict, current=None, around=None) -> None:
    """Print every file of the lesson, or only the lines around gap `around`."""
    status_color = {"ok": C.GREEN, "helped": C.YELLOW, "shown": C.RED}

    def fill(n: int):
        if n in results:
            text = lesson.gaps[n].answer
            return text, f"{status_color[results[n]]}{C.BOLD}{text}{C.RESET}"
        if n == current:
            text = f"[>>{n}<<]"
            return text, f"{C.YELLOW}{C.BOLD}{text}{C.RESET}"
        text = f"[__{n}__]"
        return text, f"{C.DIM}{text}{C.RESET}"

    for fname, code in lesson.files:
        lines = code.split("\n")
        lo, hi = 0, len(lines)
        if around is not None:
            hits = [i for i, line in enumerate(lines) if "{{%d}}" % around in line]
            if not hits:
                continue
            lo, hi = max(0, hits[0] - 3), min(len(lines), hits[0] + 4)
        print(f"  {C.DIM}// {fname}{C.RESET}")
        for i in range(lo, hi):
            here = current is not None and "{{%d}}" % current in lines[i]
            marker = f"   {C.YELLOW}{C.BOLD}<== gap {current}{C.RESET}" if here else ""
            print(f"  {C.DIM}{i + 1:>3} |{C.RESET} {_render_code_line(lines[i], fill)}{marker}")


def read_line(prompt: str):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def ask_gap(lesson: Lesson, results: dict, n: int, idx: int, total: int):
    """Returns "ok" (first try), "helped" (hint or retries), "shown", or None to quit."""
    gap = lesson.gaps[n]
    print()
    rule(f"gap {idx}/{total}")
    print_lesson_code(lesson, results, current=n, around=n)
    print()
    accepted = [answer_tokens(a) for a in [gap.answer] + gap.accept]
    wrongs = [(answer_tokens(w), feedback) for w, feedback in gap.wrong]
    tries, hinted = 0, False
    while True:
        line = read_line(f"  {C.YELLOW}{C.BOLD}gap {n}{C.RESET} > ")
        if line is None:
            return None
        text = line.strip()
        if not text:
            continue
        if text.lower() in (":q", ":quit"):
            return None
        if text.lower() in (":code", ":c"):
            print()
            print_lesson_code(lesson, results, current=n)
            print()
            continue
        if text == "?":
            print_feedback("hint:", C.CYAN, gap.hint)
            hinted = True
            continue
        if text == "!":
            status = "shown"
            break
        tokens = answer_tokens(text)
        if tokens in accepted:
            status = "helped" if tries or hinted else "ok"
            print(f"  {C.GREEN}{C.BOLD}correct!{C.RESET}")
            break
        tries += 1
        feedback = next((fb for w, fb in wrongs if w == tokens), "")
        print_feedback("not quite." if not feedback else "not quite:", C.RED, feedback)
        if tries >= 3:
            status = "shown"
            break
        if not hinted:
            print_feedback("hint:", C.CYAN, gap.hint)
            hinted = True
        elif tries == 2:
            print(f"  {C.DIM}one more try - or ! to see the answer{C.RESET}")

    color = {"ok": C.GREEN, "helped": C.YELLOW, "shown": C.RED}[status]
    print(f"\n  answer: {color}{C.BOLD}{gap.answer}{C.RESET}")
    if gap.accept:
        print(f"  {C.DIM}also accepted: {'   '.join(gap.accept)}{C.RESET}")
    print()
    print(f"  {C.BOLD}{C.MAGENTA}WHY{C.RESET}")
    print_text(gap.explanation)
    print()
    label = "next gap" if idx < total else "see the complete solution"
    line = read_line(f"  {C.DIM}Enter = {label}{C.RESET} ")
    if line is None or line.strip().lower() in (":q", ":quit"):
        return None
    return status


def run_lesson(ex: Exercise, lesson: Lesson):
    """Walk through every gap of a lesson. Returns {gap: status} or None if the user quit."""
    clear_screen()
    print()
    rule(f"fill the gap: {ex.name}")
    print(f"\n  {C.BOLD}{C.MAGENTA}THE IDEA{C.RESET}\n")
    print_text(lesson.intro)
    print()
    rule()
    print(f"  Type the code that goes in each gap (spacing doesn't matter).")
    print(f"  {C.BOLD}?{C.RESET} hint   {C.BOLD}!{C.RESET} show the answer   "
          f"{C.BOLD}:code{C.RESET} whole file   {C.BOLD}:q{C.RESET} quit")
    if read_line(f"  {C.DIM}Enter = show the code{C.RESET} ") is None:
        return None
    print()
    print_lesson_code(lesson, {}, current=lesson.order[0])
    results = {}
    for idx, n in enumerate(lesson.order, 1):
        status = ask_gap(lesson, results, n, idx, len(lesson.order))
        if status is None:
            return None
        results[n] = status

    clear_screen()
    print()
    rule(f"complete solution: {ex.name}")
    print()
    print_lesson_code(lesson, results)
    print()
    rule("the big picture")
    print()
    print_text(lesson.outro)
    print()
    counts = {s: sum(1 for v in results.values() if v == s) for s in ("ok", "helped", "shown")}
    print(f"  score: {C.GREEN}{counts['ok']} first try{C.RESET}, {C.YELLOW}{counts['helped']} with help"
          f"{C.RESET}, {C.RED}{counts['shown']} shown{C.RESET}   (out of {len(lesson.order)} gaps)")
    return results


def record_lesson_result(ex: Exercise, lesson: Lesson, results: dict) -> None:
    try:
        progress = json.loads(GAP_PROGRESS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        progress = {}
    entry = progress.setdefault(ex.name, {"best": 0, "runs": 0})
    first_try = sum(1 for v in results.values() if v == "ok")
    entry.update(best=max(entry["best"], first_try), total=len(lesson.order),
                 runs=entry["runs"] + 1, last=time.strftime("%Y-%m-%d %H:%M"))
    PRACTICE_DIR.mkdir(parents=True, exist_ok=True)
    GAP_PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def fill_the_gap_menu(tools: Toolchain, exercises: list, start_with: str = "") -> None:
    lessons = [(ex, load_lesson(ex)) for ex in exercises]
    lessons = [(ex, lesson) for ex, lesson in lessons if lesson and lesson.order]
    if not lessons:
        print("  no lessons found (exercises/*/*/gaps.txt)")
        return
    pending = start_with
    while True:
        if pending:
            choice, pending = pending, ""
        else:
            clear_screen()
            print()
            rule("fill the gap")
            print()
            print_text("You get a real solution with holes in its most important lines. Fill in the "
                       "missing code, and after each gap read WHY it's written that way - the syntax, "
                       "and the idea behind the algorithm.")
            print()
            try:
                progress = json.loads(GAP_PROGRESS_FILE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                progress = {}
            print(f"  {C.DIM}{'#':>3}  {'exercise':<20}{'gaps':<7}best run{C.RESET}")
            for i, (ex, lesson) in enumerate(lessons, 1):
                if i == 1 or lessons[i - 2][0].level != ex.level:
                    print(f"  {C.MAGENTA}{C.BOLD}level {ex.level}{C.RESET}")
                p = progress.get(ex.name)
                if p:
                    color = C.GREEN if p["best"] == len(lesson.order) else C.YELLOW
                    best = f"{color}{p['best']}/{len(lesson.order)} first try{C.RESET}"
                else:
                    best = f"{C.DIM}-{C.RESET}"
                print(f"  {i:>3}  {ex.name:<20}{len(lesson.order):<7}{best}")
            print()
            choice = ask(f"  {C.CYAN}pick # or name{C.RESET} {C.DIM}(Enter = back){C.RESET}> ").lower()
            if not choice:
                return
        matches = [(ex, l) for i, (ex, l) in enumerate(lessons, 1)
                   if choice == str(i) or ex.name == choice]
        matches = matches or [(ex, l) for ex, l in lessons if ex.name.startswith(choice)]
        if len(matches) != 1:
            ask(f"  no (unique) exercise matches '{choice}' - press Enter ")
            continue
        ex, lesson = matches[0]
        results = run_lesson(ex, lesson)
        if results is None:
            continue
        record_lesson_result(ex, lesson, results)
        after = ask(f"\n  {C.DIM}Enter = back to the list    p = now write it yourself (practice mode){C.RESET} ")
        if after.lower() == "p":
            shell = PracticeShell(tools, exercises)
            shell.select(ex, quiet=True)
            shell.start()


# --------------------------------------------------------------------------- #
#  Shared helpers for the learning modes
# --------------------------------------------------------------------------- #

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def pick_exercise(title: str, intro: str, header: str, rows: list, extra=None):
    """rows: [(exercise, info text)]. Returns an Exercise, a key of `extra`, or None (back)."""
    extra = extra or {}
    while True:
        clear_screen()
        print()
        rule(title)
        print()
        print_text(intro)
        print()
        print(f"  {C.DIM}{'#':>3}  {'exercise':<20}{header}{C.RESET}")
        last_level = None
        for i, (ex, info) in enumerate(rows, 1):
            if ex.level != last_level:
                last_level = ex.level
                print(f"  {C.MAGENTA}{C.BOLD}level {ex.level}{C.RESET}")
            print(f"  {i:>3}  {ex.name:<20}{info}")
        for key, label in extra.items():
            print(f"  {C.BOLD}{key:>3}{C.RESET}  {label}")
        print()
        choice = ask(f"  {C.CYAN}pick # or name{C.RESET} {C.DIM}(Enter = back){C.RESET}> ").lower()
        if not choice:
            return None
        if choice in extra:
            return choice
        matches = [ex for i, (ex, _) in enumerate(rows, 1) if choice in (str(i), ex.name)]
        matches = matches or [ex for ex, _ in rows if ex.name.startswith(choice)]
        if len(matches) == 1:
            return matches[0]
        ask(f"  no (unique) exercise matches '{choice}' - press Enter ")


def lesson_solution(lesson: Lesson, overrides=None) -> list:
    """The lesson's files with every gap filled (with the answer, or an override)."""
    overrides = overrides or {}

    def fill(m):
        n = int(m.group(1))
        return overrides.get(n, lesson.gaps[n].answer)

    return [(fname, GAP_MARK_RE.sub(fill, code)) for fname, code in lesson.files]


def grade_files(ex: Exercise, files: list, tools: Toolchain) -> GradeResult:
    folder = BUILD_DIR / "snippets" / f"{ex.name}-{time.time_ns()}"
    folder.mkdir(parents=True)
    for fname, text in files:
        (folder / fname).write_text(text + "\n", encoding="utf-8")
    return grade(ex, folder, tools)


# --------------------------------------------------------------------------- #
#  Find the bug
# --------------------------------------------------------------------------- #

BUG_CACHE_FILE = EXERCISES_DIR / "bug_cache.json"
BUG_PROGRESS_FILE = PRACTICE_DIR / "find_the_bug.json"
PLAYABLE_FAILURES = ("Wrong output", "Crash", "Timeout")
BUG_RANK = {"shown": 0, "fixed": 1, "clean": 2}


@dataclass
class Bug:
    """A lesson solution with one gap filled with a known wrong answer."""
    ex: Exercise
    lesson: Lesson
    gap: Gap
    index: int
    wrong: str
    feedback: str

    @property
    def key(self) -> str:
        return f"{self.gap.number}:{self.index}"

    def files(self) -> list:
        return lesson_solution(self.lesson, {self.gap.number: self.wrong})

    def location(self):
        """(file index, line index) of the line containing the bug."""
        for fi, (_, code) in enumerate(self.lesson.files):
            for li, line in enumerate(code.split("\n")):
                if "{{%d}}" % self.gap.number in line:
                    return fi, li
        raise ValueError(f"gap {self.gap.number} not found")

    def cache_key(self) -> str:
        h = hashlib.sha1(self.ex.name.encode())
        for _, text in self.files():
            h.update(text.encode())
        for extra in (self.ex.path / "config.json", self.ex.path / "tester" / "main.c"):
            if extra.is_file():
                # normalize line endings: a git checkout may use LF or CRLF
                h.update(extra.read_bytes().replace(b"\r\n", b"\n"))
        return h.hexdigest()[:20]


def exercise_bugs(ex: Exercise, lesson: Lesson, cache: dict) -> list:
    """Every wrong answer of the lesson that compiles but fails at runtime (as far as we know)."""
    bugs = []
    for n in lesson.order:
        for i, (wrong, feedback) in enumerate(lesson.gaps[n].wrong):
            bug = Bug(ex, lesson, lesson.gaps[n], i, wrong, feedback)
            verdict = cache.get(bug.cache_key())
            if verdict and (verdict["passed"] or verdict["reason"] not in PLAYABLE_FAILURES):
                continue
            bugs.append(bug)
    return bugs


def bug_verdict(bug: Bug, tools: Toolchain, cache: dict) -> dict:
    key = bug.cache_key()
    if key not in cache:
        result = grade_files(bug.ex, bug.files(), tools)
        playable = not result.passed and result.reason in PLAYABLE_FAILURES
        # only playable bugs need their trace (compiler errors would contain local paths)
        cache[key] = {"passed": result.passed, "reason": result.reason,
                      "details": ANSI_RE.sub("", result.details) if playable else ""}
        save_json(BUG_CACHE_FILE, cache)
    return cache[key]


def play_bug(bug: Bug, tools: Toolchain, cache: dict, number: int, total: int):
    """Returns "clean", "fixed", "shown", "skip" (not a runtime bug after all) or None (quit)."""
    sys.stdout.write(f"\r  {C.DIM}running the grader on the next buggy solution...{C.RESET}")
    sys.stdout.flush()
    verdict = bug_verdict(bug, tools, cache)
    sys.stdout.write("\r" + " " * 70 + "\r")
    if verdict["passed"] or verdict["reason"] not in PLAYABLE_FAILURES:
        return "skip"
    files = bug.files()
    fi, li = bug.location()
    fname, text = files[fi]
    lines = text.split("\n")

    def show_code():
        print(f"  {C.DIM}// {fname}{C.RESET}")
        for i, line in enumerate(lines):
            print(f"  {C.DIM}{i + 1:>3} |{C.RESET} {line.expandtabs(4)}")
        others = [f for j, (f, _) in enumerate(files) if j != fi]
        if others:
            print(f"  {C.DIM}({', '.join(others)} is correct){C.RESET}")

    clear_screen()
    print()
    rule(f"find the bug: {bug.ex.name}   ({number}/{total})")
    print(f"\n  This {fname} compiles, but the grader says:\n")
    print(f"  {C.RED}{C.BOLD}FAILURE{C.RESET}  {C.BOLD}{verdict['reason']}{C.RESET}")
    print(verdict["details"])
    print()
    show_code()
    print()
    print(f"  {C.DIM}type the line number of the bug   ! = show it   :code = show the code again   :q = quit{C.RESET}")

    line_tries, found = 0, False
    while True:
        raw = read_line(f"  {C.YELLOW}{C.BOLD}bug on line{C.RESET} > ")
        if raw is None:
            return None
        answer = raw.strip().lower()
        if not answer:
            continue
        if answer in (":q", ":quit"):
            return None
        if answer in (":code", ":c"):
            print()
            show_code()
            continue
        if answer == "!":
            break
        if not answer.isdigit():
            print("  type a line number")
            continue
        if int(answer) == li + 1:
            found = True
            print(f"  {C.GREEN}{C.BOLD}yes - line {li + 1}!{C.RESET}")
            break
        line_tries += 1
        if line_tries == 1:
            print_feedback(f"line {answer} is fine.", C.RED, "Compare expected with yours: what exactly is "
                           "different, and which line decides that?")
        elif line_tries == 2:
            print_feedback("not that one either.", C.RED,
                           f"hint: the bug is between lines {max(1, li - 1)} and {min(len(lines), li + 3)}.")
        else:
            break
    if not found:
        print(f"  the bug is on line {C.BOLD}{li + 1}{C.RESET}")

    buggy = lines[li]
    indent = buggy[:len(buggy) - len(buggy.lstrip())]
    template = bug.lesson.files[fi][1].split("\n")[li]
    accepted = []
    for variant in [bug.gap.answer] + bug.gap.accept:
        lesson_line = GAP_MARK_RE.sub(
            lambda m: variant if int(m.group(1)) == bug.gap.number else bug.lesson.gaps[int(m.group(1))].answer,
            template)
        accepted.append(answer_tokens(lesson_line))
    correct_line = lesson_solution(bug.lesson)[fi][1].split("\n")[li].strip()

    print(f"\n  {C.DIM}{li + 1:>3} |{C.RESET} {C.RED}{buggy.strip()}{C.RESET}")
    print(f"  Now fix it: type the whole corrected line  {C.DIM}(! = show the fix){C.RESET}")
    fix_tries, fixed = 0, False
    while fix_tries < 3:
        raw = read_line(f"  {C.YELLOW}{C.BOLD}fixed line{C.RESET} > ")
        if raw is None:
            return None
        typed = raw.strip()
        if not typed:
            continue
        if typed.lower() in (":q", ":quit"):
            return None
        if typed == "!":
            break
        if answer_tokens(typed) in accepted:
            fixed = True
        else:
            sys.stdout.write(f"  {C.DIM}grading your fix...{C.RESET}")
            sys.stdout.flush()
            patched = lines[:li] + [indent + typed] + lines[li + 1:]
            new_files = [(f, "\n".join(patched) if j == fi else t) for j, (f, t) in enumerate(files)]
            result = grade_files(bug.ex, new_files, tools)
            sys.stdout.write("\r" + " " * 40 + "\r")
            fixed = result.passed
            if not fixed:
                print(f"  {C.RED}{C.BOLD}FAILURE{C.RESET}  {C.BOLD}{result.reason}{C.RESET}")
                print(result.details)
        if fixed:
            print(f"  {C.GREEN}{C.BOLD}SUCCESS - bug fixed!{C.RESET}")
            break
        fix_tries += 1

    status = "clean" if fixed and found and not line_tries and not fix_tries else "fixed" if fixed else "shown"
    print()
    print(f"  {C.BOLD}{C.MAGENTA}THE BUG{C.RESET}")
    print_text(bug.feedback)
    print()
    print(f"  buggy  : {C.RED}{buggy.strip()}{C.RESET}")
    print(f"  correct: {C.GREEN}{correct_line}{C.RESET}")
    print()
    print(f"  {C.BOLD}{C.MAGENTA}WHY{C.RESET}")
    print_text(bug.gap.explanation)
    print()
    return status


def run_bug_session(bugs: list, tools: Toolchain, cache: dict) -> None:
    progress = load_json(BUG_PROGRESS_FILE, {})
    total = len(bugs)
    for number, bug in enumerate(bugs, 1):
        status = play_bug(bug, tools, cache, number, total)
        if status is None:
            return
        if status == "skip":
            continue
        done = progress.setdefault(bug.ex.name, {})
        if BUG_RANK[status] >= BUG_RANK.get(done.get(bug.key, ""), -1):
            done[bug.key] = status
        save_json(BUG_PROGRESS_FILE, progress)
        label = "next bug" if number < total else "back to the list"
        raw = read_line(f"  {C.DIM}Enter = {label}   :q = stop{C.RESET} ")
        if raw is None or raw.strip().lower() in (":q", ":quit", "q"):
            return


def bugs_in_order(bugs: list, progress: dict) -> list:
    """Unsolved bugs first (random order), then the already fixed ones."""
    def solved(b):
        return progress.get(b.ex.name, {}).get(b.key) in ("clean", "fixed")
    todo = [b for b in bugs if not solved(b)]
    done = [b for b in bugs if solved(b)]
    random.shuffle(todo)
    random.shuffle(done)
    return todo + done


def play_exercise_bugs(tools: Toolchain, ex: Exercise) -> None:
    lesson = load_lesson(ex)
    if not lesson or not lesson.order:
        print("  no bugs for this exercise")
        return
    cache = load_json(BUG_CACHE_FILE, {})
    bugs = exercise_bugs(ex, lesson, cache)
    run_bug_session(bugs_in_order(bugs, load_json(BUG_PROGRESS_FILE, {})), tools, cache)


def find_the_bug_menu(tools: Toolchain, exercises: list, start_with: str = "") -> None:
    lessons = [(ex, load_lesson(ex)) for ex in exercises]
    lessons = [(ex, lesson) for ex, lesson in lessons if lesson and lesson.order]
    if start_with:
        match = [ex for ex, _ in lessons if ex.name.startswith(start_with)]
        if len(match) == 1:
            play_exercise_bugs(tools, match[0])
    while True:
        cache = load_json(BUG_CACHE_FILE, {})
        progress = load_json(BUG_PROGRESS_FILE, {})
        rows, all_bugs = [], []
        for ex, lesson in lessons:
            bugs = exercise_bugs(ex, lesson, cache)
            all_bugs += bugs
            fixed = sum(1 for b in bugs if progress.get(ex.name, {}).get(b.key) in ("clean", "fixed"))
            color = C.GREEN if bugs and fixed == len(bugs) else C.YELLOW if fixed else C.DIM
            rows.append((ex, f"{len(bugs):<7}{color}{fixed}/{len(bugs)} fixed{C.RESET}"))
        choice = pick_exercise(
            "find the bug",
            "Each puzzle is a solution that compiles but FAILS - you get the grader's trace (expected vs "
            "yours) and the code. Find the line with the bug, then type the fixed line: the grader checks "
            "your fix. Reading a trace and tracking down the line is exactly what you do at the exam.",
            "bugs   progress", rows, {"r": "random bugs from all exercises"})
        if choice is None:
            return
        if choice == "r":
            run_bug_session(bugs_in_order(all_bugs, progress), tools, cache)
        else:
            play_exercise_bugs(tools, choice)


# --------------------------------------------------------------------------- #
#  Predict the output
# --------------------------------------------------------------------------- #

PREDICT_PROGRESS_FILE = PRACTICE_DIR / "predict.json"


@dataclass
class Question:
    body: str
    answer: str
    accept: list
    wrong: list          # [(answer, feedback)]
    match: str           # "tokens" (default), "exact" (cat -e output) or "text"
    args: object         # program arguments, used to verify the answer
    explanation: str

    def normalize(self, text: str):
        if self.match == "exact":
            return text.rstrip()
        if self.match == "text":
            return " ".join(text.lower().split())
        return [{"[": "{", "]": "}"}.get(t, t) for t in answer_tokens(text)]

    def is_correct(self, text: str) -> bool:
        return self.normalize(text) in [self.normalize(a) for a in [self.answer] + self.accept]

    def feedback_for(self, text: str) -> str:
        return next((fb for w, fb in self.wrong if self.normalize(w) == self.normalize(text)), "")

    def missing_dollar(self, text: str) -> bool:
        return self.match == "exact" and self.answer.endswith("$") and \
            self.answer in (text + "$", text.rstrip() + "$")


def load_questions(ex: Exercise) -> list:
    """Parse exercises/<level>/<name>/predict.txt: @@ question blocks with answer:/accept:/
    wrong:/match:/args: lines, the question, a '---' line, then the explanation."""
    path = ex.path / "predict.txt"
    if not path.is_file():
        return []
    blocks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("@@ "):
            blocks.append([])
        elif blocks:
            blocks[-1].append(line)
    questions = []
    for lines in blocks:
        q = Question("", "", [], [], "tokens", None, "")
        k = 0
        while k < len(lines) and re.match(r"(answer|accept|wrong|match|args):", lines[k]):
            key, _, value = lines[k].partition(":")
            value = value[1:] if value.startswith(" ") else value   # keep other spaces: they matter for exact
            if key == "answer":
                q.answer = value
            elif key == "accept":
                q.accept.append(value)
            elif key == "match":
                q.match = value.strip()
            elif key == "args":
                q.args = json.loads(value)
            else:
                wrong, _, feedback = value.partition(" => ")
                q.wrong.append((wrong, feedback.strip()))
            k += 1
        rest = lines[k:]
        sep = rest.index("---") if "---" in rest else len(rest)
        q.body = "\n".join(rest[:sep]).strip("\n")
        q.explanation = "\n".join(rest[sep + 1:]).strip("\n")
        questions.append(q)
    return questions


def run_quiz(title: str, items: list):
    """items: [(exercise, question)]. Returns the number of first-try answers, or None if quit."""
    clear_screen()
    print()
    rule(title)
    print()
    print_text("Type exactly what comes out. Program output is written the way `cat -e` shows it: `$` marks "
               "the end of the line, so a lone `$` means \"just a newline\" - and spaces count. For functions, "
               "spacing doesn't matter.")
    print(f"\n  {C.DIM}! = show the answer   :q = quit{C.RESET}")
    score = 0
    for number, (ex, q) in enumerate(items, 1):
        print()
        rule(f"{number}/{len(items)}   {ex.name}")
        print()
        print_text(q.body)
        print()
        tries, correct = 0, False
        while True:
            raw = read_line(f"  {C.YELLOW}{C.BOLD}>{C.RESET} ")
            if raw is None:
                return None
            if not raw.strip():
                continue
            if raw.strip().lower() in (":q", ":quit"):
                return None
            if raw.strip() == "!":
                break
            if q.is_correct(raw):
                correct = True
                print(f"  {C.GREEN}{C.BOLD}correct!{C.RESET}")
                break
            if q.missing_dollar(raw):
                print_feedback("almost:", C.YELLOW, "add the `$` - the output ends with a newline.")
                continue
            tries += 1
            feedback = q.feedback_for(raw)
            print_feedback("not quite:" if feedback else "not quite.", C.RED, feedback)
            if tries >= 2:
                break
            print(f"  {C.DIM}one more try - or ! to see the answer{C.RESET}")
        if correct and not tries:
            score += 1
        color = C.GREEN if correct else C.RED
        print(f"\n  answer: {color}{C.BOLD}{q.answer}{C.RESET}")
        print()
        print(f"  {C.BOLD}{C.MAGENTA}WHY{C.RESET}")
        print_text(q.explanation)
        print()
        label = "next question" if number < len(items) else "see your score"
        raw = read_line(f"  {C.DIM}Enter = {label}{C.RESET} ")
        if raw is None or raw.strip().lower() in (":q", ":quit"):
            return None
    print()
    rule("score")
    color = C.GREEN if score == len(items) else C.YELLOW
    print(f"\n  {color}{C.BOLD}{score}/{len(items)}{C.RESET} right on the first try\n")
    return score


def play_exercise_quiz(ex: Exercise) -> None:
    questions = load_questions(ex)
    if not questions:
        print("  no questions for this exercise")
        return
    score = run_quiz(f"predict the output: {ex.name}", [(ex, q) for q in questions])
    if score is None:
        return
    progress = load_json(PREDICT_PROGRESS_FILE, {})
    entry = progress.setdefault(ex.name, {"best": 0})
    entry.update(best=max(entry["best"], score), total=len(questions), last=time.strftime("%Y-%m-%d %H:%M"))
    save_json(PREDICT_PROGRESS_FILE, progress)
    ask(f"  {C.DIM}press Enter{C.RESET} ")


def predict_menu(tools: Toolchain, exercises: list, start_with: str = "") -> None:
    sets = [(ex, load_questions(ex)) for ex in exercises]
    sets = [(ex, qs) for ex, qs in sets if qs]
    if start_with:
        match = [ex for ex, _ in sets if ex.name.startswith(start_with)]
        if len(match) == 1:
            play_exercise_quiz(match[0])
    while True:
        progress = load_json(PREDICT_PROGRESS_FILE, {})
        rows = []
        for ex, qs in sets:
            p = progress.get(ex.name)
            if p:
                color = C.GREEN if p["best"] == len(qs) else C.YELLOW
                info = f"{len(qs):<12}{color}best {p['best']}/{len(qs)}{C.RESET}"
            else:
                info = f"{len(qs):<12}{C.DIM}-{C.RESET}"
            rows.append((ex, info))
        choice = pick_exercise(
            "predict the output",
            "Tricky inputs - you type the exact output, then read why. Most exam FAILUREs aren't bad "
            "algorithms but details of the subject: a missing newline, an extra space, the number of "
            "arguments, tabs...",
            "questions   best", rows, {"a": "all exercises mixed (15 random questions)"})
        if choice is None:
            return
        if choice == "a":
            pool = [(ex, q) for ex, qs in sets for q in qs]
            if run_quiz("predict the output: mixed", random.sample(pool, min(15, len(pool)))) is not None:
                ask(f"  {C.DIM}press Enter{C.RESET} ")
        else:
            play_exercise_quiz(choice)


# --------------------------------------------------------------------------- #
#  Entry points
# --------------------------------------------------------------------------- #

def ask_exam_setup():
    """Returns (levels, minutes) or None."""
    levels = sorted({e.level for e in load_exercises()})
    print()
    print(f"  {C.BOLD}Enter{C.RESET}   full Exam Rank 02: levels {levels[0]} -> {levels[-1]} "
          f"(pass = next level, {FULL_EXAM_MINUTES} min)")
    print(f"  {C.BOLD}1-{levels[-1]}{C.RESET}     only that level ({DEFAULT_EXAM_MINUTES} min)")
    raw = ask(f"  {C.CYAN}exam{C.RESET}> ").lower()
    if raw in ("q", "quit", "back"):
        return None
    chosen = [int(raw)] if raw.isdigit() and int(raw) in levels else levels
    default = FULL_EXAM_MINUTES if len(chosen) > 1 else DEFAULT_EXAM_MINUTES
    raw = ask(f"  duration in minutes {C.DIM}[{default}]{C.RESET}: ")
    return chosen, (int(raw) if raw.isdigit() and int(raw) > 0 else default)


def start_exam(tools: Toolchain, exercises: list, minutes=None, levels=None) -> None:
    state = ExamShell.load_state()
    if state and state["start"] + state["minutes"] * 60 > time.time():
        left = fmt_duration(state["start"] + state["minutes"] * 60 - time.time())
        if confirm(f"  An exam is running ({state['current']}, {left} left). Resume it?"):
            ExamShell(tools, exercises, state).start()
            return
        if not confirm("  Abandon it and start a new exam?"):
            return
        ExamShell(tools, exercises, state).finish(False, "abandoned")
    elif state:
        ExamShell(tools, exercises, state).finish(False, "time is up")
    if levels is None and minutes is None:
        setup = ask_exam_setup()
        if setup is None:
            return
        levels, minutes = setup
    all_levels = sorted({e.level for e in exercises})
    levels = levels or all_levels
    if minutes is None:
        minutes = FULL_EXAM_MINUTES if len(levels) > 1 else DEFAULT_EXAM_MINUTES
    ExamShell.new(tools, exercises, minutes, levels).start()


def main_menu(tools: Toolchain, exercises: list) -> None:
    while True:
        clear_screen()
        levels = sorted({e.level for e in exercises})
        print_banner(f"{C.DIM}{len(exercises)} exercises in {len(levels)} levels - "
                     f"compiler: {tools.describe()}{C.RESET}")
        state = ExamShell.load_state()
        resume = ""
        if state and state["start"] + state["minutes"] * 60 > time.time():
            resume = f"  {C.YELLOW}(exam running: {state['current']}, " \
                     f"{fmt_duration(state['start'] + state['minutes'] * 60 - time.time())} left){C.RESET}"
        print(f"   {C.BOLD}1{C.RESET}  Exam mode      levels 1 -> 4 with a timer, unlimited retries with the trace{resume}")
        print(f"   {C.BOLD}2{C.RESET}  Practice mode  choose any exercise, retry as often as you want")
        print(f"   {C.BOLD}3{C.RESET}  Fill the gap   complete the key lines of a solution and learn why they work")
        print(f"   {C.BOLD}4{C.RESET}  Find the bug   read the grader's trace, find the broken line, fix it")
        print(f"   {C.BOLD}5{C.RESET}  Predict        type the exact output for tricky inputs (spaces, newlines, argc...)")
        print(f"   {C.BOLD}q{C.RESET}  Quit")
        print()
        choice = ask(f"  {C.CYAN}choice{C.RESET}> ").lower()
        if choice == "1":
            start_exam(tools, exercises)
        elif choice == "2":
            PracticeShell(tools, exercises).start()
        elif choice == "3":
            fill_the_gap_menu(tools, exercises)
        elif choice == "4":
            find_the_bug_menu(tools, exercises)
        elif choice == "5":
            predict_menu(tools, exercises)
        elif choice in ("q", "quit", "exit"):
            return


def run_check(tools: Toolchain, exercises: list) -> int:
    """`examshell.bat check`: verify the whole toolchain by grading two reference solutions."""
    def line(ok: bool, label: str, detail: str = "") -> None:
        mark = f"{C.GREEN}[ OK ]{C.RESET}" if ok else f"{C.RED}[FAIL]{C.RESET}"
        print(f"  {mark} {label:<22}{detail}")

    print()
    rule("examshell check")
    line(True, "Python", sys.version.split()[0])
    line(True, "C compiler", f"{tools.describe()}  ({tools.cc})")
    levels = sorted({e.level for e in exercises})
    lessons = sum(1 for e in exercises if (e.path / "gaps.txt").is_file())
    line(True, "exercises", f"{len(exercises)} in levels {levels[0]}-{levels[-1]}, {lessons} lessons")
    try:
        tools.runtime_obj()
        line(True, "compile test")
    except (RuntimeError, OSError) as err:
        line(False, "compile test", str(err).splitlines()[0])
        print(f"\n  gcc is installed but can't compile. Reinstall it with:\n"
              f"    winget install BrechtSanders.WinLibs.POSIX.UCRT\n")
        return 1
    failed = False
    for ex in [e for e in exercises if e.kind == "program"][:1] + [e for e in exercises if e.kind == "function"][:1]:
        files = [(p.name, p.read_text(encoding="utf-8")) for p in (ex.path / "ref").iterdir()]
        try:
            result = grade_files(ex, files, tools)
        except (RuntimeError, OSError) as err:
            line(False, f"grade {ex.name}", str(err).splitlines()[0])
            failed = True
            continue
        line(result.passed, f"grade {ex.name}", result.reason)
        if not result.passed:
            print(ANSI_RE.sub("", result.details))
            failed = True
    rule()
    if failed:
        print(f"  {C.RED}Something is wrong with the setup - see above.{C.RESET}\n")
        return 1
    print(f"  {C.GREEN}{C.BOLD}Everything works.{C.RESET} Start examshell.bat and pick a mode.\n")
    return 0


def main(argv: list) -> int:
    enable_colors()
    silence_crash_dialogs()
    exercises = load_exercises()
    if not exercises:
        print(f"no exercises found in {EXERCISES_DIR}")
        return 1
    cc = find_compiler()
    if not cc:
        print(f"{C.RED}No C compiler found.{C.RESET} Install gcc (MinGW-w64), e.g. in a terminal:\n\n"
              f"    winget install BrechtSanders.WinLibs.POSIX.UCRT\n\n"
              f"then open a NEW terminal and run:  examshell.bat check\n"
              f"(or set EXAMSHELL_CC to the full path of gcc.exe)")
        return 1
    tools = Toolchain(cc)
    # clean old build folders - only stale ones: another examshell window may be grading right now
    for sub in ("user", "snippets"):
        for old in (BUILD_DIR / sub).glob("*"):
            try:
                if time.time() - old.stat().st_mtime > 3600:
                    shutil.rmtree(old, ignore_errors=True)
            except OSError:
                pass

    cmd = argv[0].lower() if argv else ""
    if cmd in ("check", "doctor", "setup"):
        return run_check(tools, exercises)
    if cmd == "grade":
        if len(argv) != 3 or argv[1] not in {e.name for e in exercises}:
            print("usage: examshell grade <exercise> <folder>")
            print("exercises: " + ", ".join(e.name for e in exercises))
            return 2
        ex = next(e for e in exercises if e.name == argv[1])
        result = grade(ex, Path(argv[2]).resolve(), tools)
        print_grade_result(result)
        return 0 if result.passed else 1
    try:
        if cmd == "exam":
            numbers = [int(a) for a in argv[1:] if a.isdigit()]
            level = next((n for n in numbers if 1 <= n <= 4), None)
            minutes = next((n for n in numbers if n > 4), None)
            if level is None and minutes is None:
                start_exam(tools, exercises)
            else:
                start_exam(tools, exercises, minutes, [level] if level else None)
        elif cmd == "practice":
            shell = PracticeShell(tools, exercises)
            if len(argv) > 1:
                shell.cmd_pick(argv[1:])
            shell.start()
        elif cmd in ("gaps", "gap", "learn"):
            fill_the_gap_menu(tools, exercises, argv[1].lower() if len(argv) > 1 else "")
        elif cmd in ("bugs", "bug"):
            find_the_bug_menu(tools, exercises, argv[1].lower() if len(argv) > 1 else "")
        elif cmd in ("predict", "quiz"):
            predict_menu(tools, exercises, argv[1].lower() if len(argv) > 1 else "")
        else:
            main_menu(tools, exercises)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        import traceback
        traceback.print_exc()
        if sys.stdin.isatty():
            ask("\nexamshell crashed (see above) - press Enter to close ")
        sys.exit(1)
