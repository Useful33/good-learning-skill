"""Normalise bare sub/superscripts in study Markdown into real LaTeX math.

The study renderer escapes text, so `A_1` written outside math mode prints a
literal underscore.  This pass finds maximal "math-ish" runs (letters, digits,
math punctuation, Unicode math symbols) that contain at least one math marker
(`_`, `^`, a Unicode math symbol, or a star superscript), rewrites each run as
LaTeX math and wraps it in `$...$`.  Because the whole run is wrapped, adjacent
operators and parentheses also end up inside math mode, matching the textbook.

Protected from rewriting: existing `$...$` / `$$...$$`, backtick code spans and
Markdown links.  Markdown `**bold**` delimiters are replaced by sentinels so a
run cannot span a bold boundary, and stars are emitted as `^{\\ast}` so that no
`*` ever appears inside a bold span (the renderer's bold regex forbids it).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

SENTINEL = "\x00"
AST = "\x01"

MATH_SPAN = re.compile(r"\$\$[\s\S]*?\$\$|\$[^$\n]+?\$")
CODE_SPAN = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\[[^\]\n]*\]\([^)\n]*\)")
BOLD = re.compile(r"\*\*")

# Unicode characters replaced by LaTeX macros inside a math run.
MACROS = {
    "µ": r"\mu", "μ": r"\mu", "ν": r"\nu", "σ": r"\sigma", "ς": r"\varsigma",
    "Ω": r"\Omega", "Λ": r"\Lambda", "λ": r"\lambda", "ε": r"\varepsilon",
    "δ": r"\delta", "ϕ": r"\phi", "φ": r"\varphi", "θ": r"\theta",
    "π": r"\pi", "ρ": r"\rho", "τ": r"\tau", "ξ": r"\xi", "η": r"\eta",
    "κ": r"\kappa", "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega",
    "ζ": r"\zeta", "α": r"\alpha", "β": r"\beta", "Γ": r"\Gamma",
    "Δ": r"\Delta", "Θ": r"\Theta", "Φ": r"\Phi", "Ψ": r"\Psi",
    "Σ": r"\sum", "∑": r"\sum", "Π": r"\prod", "∏": r"\prod",
    "⊂": r"\subset", "⊃": r"\supset", "⊆": r"\subseteq", "⊇": r"\supseteq",
    "∈": r"\in", "∉": r"\notin", "∋": r"\ni", "∪": r"\cup", "∩": r"\cap",
    "∅": r"\varnothing", "≤": r"\le", "≥": r"\ge", "≠": r"\ne",
    "≈": r"\approx", "∼": r"\sim", "≡": r"\equiv", "≪": r"\ll", "≫": r"\gg",
    "→": r"\to", "←": r"\leftarrow", "⇒": r"\Rightarrow",
    "⟹": r"\Longrightarrow", "⇔": r"\Leftrightarrow", "↦": r"\mapsto",
    "↑": r"\uparrow", "↓": r"\downarrow", "∞": r"\infty",
    "⋅": r"\cdot", "∘": r"\circ", "∂": r"\partial", "√": r"\surd",
    "∫": r"\int", "±": r"\pm", "×": r"\times", "÷": r"\div",
    "∖": r"\setminus", "△": r"\triangle", "∀": r"\forall", "∃": r"\exists",
    "⟨": r"\langle", "⟩": r"\rangle", "∥": r"\parallel", "∣": r"\mid",
    "−": "-", "–": "--", "—": "---", "…": r"\dots",
    "′": "'", "″": "''", "／": "/", "＝": "=",
}

MARKERS = {c for c, m in MACROS.items() if m.startswith("\\")}

MATHISH = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    " \t_^*()[]{}+-=/.,;:<>'"
) | set(MACROS)

TRAIL_TRIM = ".,;:+-=/|"
LEAD_TRIM = ".,;:+-=/|*"

STAR_AFTER = re.compile(
    r"(?<=[A-Za-z0-9µμνσΩΛλεδϕφθπρτξηκχψωζαβΓΔΘΦΨ\]\)])\*"
)
CAL_A = re.compile(r"(?<![A-Za-z\\])A\^\{\\ast\}")
SUP_PAREN = re.compile(r"\^\(([^()]*)\)")
BOLD_SPAN = re.compile(r"\*\*([^*]*)\*\*")
PLACEHOLDER = re.compile(SENTINEL + r"([0-9]+|B)" + SENTINEL)


def mask(text: str) -> tuple[str, list[str]]:
    """Replace protected spans and bold delimiters with sentinels."""
    store: list[str] = []

    def stash(match: re.Match[str]) -> str:
        store.append(match.group(0))
        return SENTINEL + str(len(store) - 1) + SENTINEL

    for pattern in (MATH_SPAN, CODE_SPAN, LINK):
        text = pattern.sub(stash, text)
    return BOLD.sub(lambda m: SENTINEL + "B" + SENTINEL, text), store


def unmask(text: str, store: list[str]) -> str:
    def restore(match: re.Match[str]) -> str:
        body = match.group(1)
        return "**" if body == "B" else store[int(body)]

    return PLACEHOLDER.sub(restore, text)


def has_marker(run: str) -> bool:
    if "_" in run or "^" in run:
        return True
    if any(char in MARKERS for char in run):
        return True
    for match in re.finditer(r"\*", run):
        before = run[: match.start()].rstrip()
        if before and before[-1].isalnum():
            return True
    return False


def escape_literal_braces(body: str) -> str:
    """Escape set braces, keeping LaTeX groups such as `_{k\\ge{}n}` intact.

    A brace opens a LaTeX group when it directly follows `_`, `^` or a control
    word; everything nested inside such a group is LaTeX as well.  Any other
    brace is a literal set brace and is escaped.
    """
    out: list[str] = []
    stack: list[bool] = []
    tail = re.compile(r"\\[A-Za-z]+$")
    for char in body:
        if char == "{":
            preceding = "".join(out[-24:])
            latex = bool(stack and stack[-1]) or (
                bool(out) and out[-1] in "_^"
            ) or bool(tail.search(preceding))
            stack.append(latex)
            out.append("{" if latex else r"\{")
        elif char == "}":
            latex = stack.pop() if stack else False
            out.append("}" if latex else r"\}")
        else:
            out.append(char)
    return "".join(out)


def expand_macros(text: str) -> str:
    """Replace Unicode symbols with macros, keeping control words separated.

    TeX ends a control word only at a non-letter, so `Σ` followed by `A` would
    produce the undefined `\\sumA`; an empty group terminates it instead.
    """
    out: list[str] = []
    for index, char in enumerate(text):
        macro = MACROS.get(char)
        if macro is None:
            out.append(char)
            continue
        out.append(macro)
        following = text[index + 1] if index + 1 < len(text) else ""
        if macro[:1] == "\\" and macro[1:].isalpha() and following.isascii() and following.isalpha():
            out.append("{}")
    return "".join(out)


def convert_run(run: str) -> str:
    lead = ""
    trail = ""
    core = run
    while core and (core[0] in LEAD_TRIM or core[0].isspace()):
        lead += core[0]
        core = core[1:]
    while core and (core[-1] in TRAIL_TRIM or core[-1].isspace()):
        trail = core[-1] + trail
        core = core[:-1]
    # Keep a leading list/sentence number out of the formula ("单元 4 µ*").
    numbered = re.match(r"\d+\s+(?=\S)", core)
    if numbered and has_marker(core[numbered.end():]):
        lead += numbered.group(0)
        core = core[numbered.end():]
    # A literal backslash would collide with the macros we insert: leave it alone.
    # A doubled underscore is a fill-in blank (and `__` is an invalid subscript).
    if not core or "\\" in core or "__" in core or not has_marker(core):
        return run
    body = core
    body = SUP_PAREN.sub(r"^{(\1)}", body)
    # Replacement callables: a template string would turn "\a" into the BEL escape.
    body = STAR_AFTER.sub(lambda _m: r"^{\ast}", body)
    body = CAL_A.sub(lambda _m: r"\mathcal{A}^{\ast}", body)
    body = expand_macros(body)
    body = body.replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")
    body = body.replace("~", r"\sim")
    body = escape_literal_braces(body)
    return lead + "$" + body + "$" + trail


def convert_runs(text: str) -> str:
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] in MATHISH:
            end = index
            while end < length and text[end] in MATHISH:
                end += 1
            out.append(convert_run(text[index:end]))
            index = end
        else:
            out.append(text[index])
            index += 1
    return "".join(out)


def process(text: str) -> tuple[str, list[str]]:
    masked, store = mask(text)
    result = unmask(convert_runs(masked), store)
    problems = [m.group(0) for m in BOLD_SPAN.finditer(result) if "*" in m.group(1)]
    return result, problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    lines: list[str] = []
    for path in args.files:
        original = path.read_text(encoding="utf-8")
        updated, problems = process(original)
        changed = sum(1 for a, b in zip(original.splitlines(), updated.splitlines()) if a != b)
        added = updated.count("$") // 2 - original.count("$") // 2
        lines.append(
            f"{path.name}: +{added} math spans, {changed} changed lines, "
            f"{len(problems)} bold problems"
        )
        for problem in problems:
            lines.append(f"    PROBLEM: {problem[:150]}")
        if not args.dry_run and updated != original:
            path.write_text(updated, encoding="utf-8")
    print("\n".join(lines))
    if args.report:
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
