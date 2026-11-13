#!/usr/bin/env python3
"""Find which curricula (grade + subject) mention a topic.

Usage:
    python find_topic.py <term> [<term> ...] [--full]

Each term is matched case-insensitively as a substring, so pass word stems
(e.g. "рек" "речн" for rivers, "квадратн" for quadratic). Prints every
programme entry from references/tematichna-karta.md that contains any term,
showing the matched snippets. With --full, prints the whole entry.
"""
import pathlib
import re
import sys

MAP_FILE = pathlib.Path(__file__).resolve().parent.parent / "references" / "tematichna-karta.md"


def entries():
    text = MAP_FILE.read_text(encoding="utf-8")
    for block in re.split(r"\n(?=### )", text):
        if block.startswith("### "):
            yield block.strip()


def main(argv):
    full = "--full" in argv
    terms = [t.lower() for t in argv if t != "--full"]
    if not terms:
        sys.exit(__doc__)
    hits = 0
    for e in entries():
        low = e.lower()
        if not any(t in low for t in terms):
            continue
        hits += 1
        lines = e.splitlines()
        print(lines[0])
        print(lines[1] if len(lines) > 1 else "")
        if full:
            print("\n".join(lines[2:]))
        else:
            for t in terms:
                for m in re.finditer(re.escape(t), low):
                    a, b = max(0, m.start() - 60), m.end() + 60
                    print(f"  …{e[a:b].replace(chr(10), ' ')}…")
                    break
        print()
    print(f"[{hits} програми]")


if __name__ == "__main__":
    main(sys.argv[1:])
