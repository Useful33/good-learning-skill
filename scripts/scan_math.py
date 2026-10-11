"""Scan study Markdown for bare sub/superscripts that are not inside math mode."""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

MATH = re.compile(r"\$\$[\s\S]*?\$\$|\$[^$\n]+?\$")
BLOCK = re.compile(r"`[^`\n]*`")
TOKEN = re.compile(r"[^\s$`]{0,8}[_^][^\s$`]{1,10}")


def main() -> None:
    for name in sys.argv[1:]:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        masked = MATH.sub(lambda m: " " * len(m.group(0)), text)
        masked = BLOCK.sub(lambda m: " " * len(m.group(0)), masked)
        counts: collections.Counter[str] = collections.Counter()
        for line in masked.splitlines():
            for m in TOKEN.finditer(line):
                counts[m.group(0)] += 1
        print(f"=== {path.name}: {len(counts)} distinct, {sum(counts.values())} total ===")
        for token, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {n:4d}  {token}")


if __name__ == "__main__":
    main()
