#!/usr/bin/env python3
"""Look up exact text in the bundled laws and regulations (references/zakon-*.txt).

Usage:
    python find_law.py <doc> <article-number>       # e.g. N11_ocenyavane 12   -> prints чл. 12
    python find_law.py <doc> "<term>"               # e.g. ZPUO "мобилни"   -> articles containing the term
    python find_law.py all "<term>"                 # search every document (lists doc + article)
    python find_law.py <doc> "§ 7"                  # a paragraph of the transitional/final provisions (all amending acts)
    python find_law.py <doc> преходни               # ALL transitional/final provisions: dates when rules start/stop applying
    python find_law.py list                         # list document keys and their header line

<doc> is a file name without .txt (case-insensitive prefix match is fine, e.g. "N11").
Matching is case-insensitive; pass a word stem to catch all forms.
"""
import pathlib
import re
import sys

DIR = pathlib.Path(__file__).resolve().parent.parent / "references"
ART = re.compile(r"\n(?=(?:Чл\. \d+[а-я]?\.|§ ?\d+[а-я]?\.|(?:Преходни|Заключителни|Допълнителни)[^\n]{0,40}разпоредби))")
CLEAN = re.compile(r"\((?:изм|нова|нов|доп|отм)\.?[^()]*?ДВ[^()]*\)", re.I)


def docs(key):
    files = sorted(DIR.glob("zakon-*.txt"))
    if key == "all":
        return files
    k = key.lower()
    exact = [f for f in files if f.stem.lower()[6:] == k]
    return exact or [f for f in files if f.stem.lower()[6:].startswith(k)]


def articles(path):
    text = path.read_text(encoding="utf-8")
    return [a.strip() for a in ART.split(text) if re.match(r"(Чл\.|§|Преходни|Заключителни|Допълнителни)", a.strip())], text


def main(a):
    if not a:
        sys.exit(__doc__)
    if a[0] == "list":
        for f in sorted(DIR.glob("zakon-*.txt")):
            t = f.read_text(encoding="utf-8")
            m = re.search(r"Обн\. ДВ[^\n]*", t)
            last = re.findall(r"ДВ\. ?бр\.?\s?\d+ от \d+ \S+ \d{4}", m.group(0)) if m else []
            print(f"{f.stem[6:]}: последно {last[-1] if last else '?'}")
        return
    if len(a) < 2:
        sys.exit(__doc__)
    files = docs(a[0])
    if not files:
        sys.exit(f"Няма документ '{a[0]}'. Използвай: find_law.py list")
    q = a[1]
    for f in files:
        arts, _ = articles(f)
        if q.startswith("§"):
            n = q.lstrip("§ ").strip()
            hit = [x for x in arts if re.match(rf"§ ?{n}\.", x)]
            for x in hit:
                print(f"== {f.stem[6:]}\n{x[:2500]}\n")
        elif q.isdigit() or re.fullmatch(r"\d+[а-я]", q):
            hit = [x for x in arts if re.match(rf"Чл\. {q}\.", x)]
            for x in hit:
                print(f"== {f.stem[6:]}\n{CLEAN.sub('', x)}\n")
        else:
            hit = [x for x in arts if q.lower() in x.lower()]
            for x in hit[:15]:
                head = x.split("\n", 1)[0][:12]
                if a[0] == "all":
                    i = x.lower().find(q.lower())
                    print(f"{f.stem[6:]} {head} …{x[max(0,i-80):i+120].replace(chr(10),' ')}…")
                else:
                    print(f"== {f.stem[6:]}\n{CLEAN.sub('', x)[:2500]}\n")
            if len(hit) > 15:
                print(f"[{f.stem[6:]}: още {len(hit)-15} члена съдържат '{q}']")


if __name__ == "__main__":
    main(sys.argv[1:])
