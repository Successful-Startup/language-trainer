#!/usr/bin/env python3
"""
Generate a words CSV file from the pymorphy2 dictionary.

This script iterates over the pymorphy2 morphological dictionary, extracts
nouns (NOUN) and full adjectives (ADJF), and writes them into a CSV file
compatible with the Language Trainer import endpoint.

Output format (words.csv):
    base_form,part_of_speech_name,gender_name
    стол,Существительное,Мужской
    большой,Прилагательное,Мужской

Usage:
    python generate_words_csv.py                           # all nouns + adjectives
    python generate_words_csv.py --pos noun                # nouns only
    python generate_words_csv.py --pos adj                 # adjectives only
    python generate_words_csv.py --limit 1000              # first 1000 per POS
    python generate_words_csv.py -o my_words.csv           # custom output path

Requirements:
    pip install pymorphy3
"""

import argparse
import csv
import re
import sys
import time

import pymorphy3

# ── pymorphy2 tag → DB name mapping ────────────────────────────────────────

POS_MAP = {
    "NOUN": "Существительное",
    "ADJF": "Прилагательное",
}

GENDER_MAP = {
    "masc": "Мужской",
    "femn": "Женский",
    "neut": "Средний",
}

SKIP_RE = re.compile(r"[-\d./]")

# pymorphy3 tags that mark proper nouns (names, surnames, patronymics, etc.)
PROPER_NOUN_TAGS = {"Name", "Surn", "Patr", "Geox", "Orgn"}


def collect_lemmas(morph, pos_tag, limit=0):
    """
    Iterate over pymorphy2 dictionary and collect unique lemmas for a POS.

    Returns list of (base_form, gender_name) tuples.
    """
    seen = set()
    lemmas = []

    for word_obj in morph.iter_known_word_forms():
        if limit and len(lemmas) >= limit:
            break

        tag = word_obj.tag
        if tag.POS != pos_tag:
            continue

        normal = word_obj.normal_form
        if normal in seen:
            continue
        if SKIP_RE.search(normal):
            continue
        if len(normal) < 2:
            continue
        # Skip proper nouns (names, surnames, patronymics, places, orgs)
        tag_str = str(tag)
        if any(t in tag_str for t in PROPER_NOUN_TAGS):
            continue

        gender_tag = str(tag.gender) if tag.gender else None

        if pos_tag == "NOUN" and gender_tag not in GENDER_MAP:
            continue
        if pos_tag == "ADJF":
            gender_tag = "masc"

        gender_name = GENDER_MAP.get(gender_tag, "")
        seen.add(normal)
        lemmas.append((normal.lower(), gender_name))

    return lemmas


def main():
    parser = argparse.ArgumentParser(description="Generate words CSV from pymorphy2")
    parser.add_argument(
        "-o",
        "--output",
        default="words.csv",
        help="Output CSV file path (default: words.csv)",
    )
    parser.add_argument(
        "--pos",
        choices=["noun", "adj", "both"],
        default="both",
        help="Part of speech to include (default: both)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max lemmas per POS (0 = no limit)",
    )
    args = parser.parse_args()

    print("Loading pymorphy2 dictionary...")
    morph = pymorphy3.MorphAnalyzer()
    print("Dictionary loaded.")

    pos_tags = []
    if args.pos in ("noun", "both"):
        pos_tags.append("NOUN")
    if args.pos in ("adj", "both"):
        pos_tags.append("ADJF")

    all_lemmas = []
    start = time.time()

    for pos_tag in pos_tags:
        print(f"Collecting {POS_MAP[pos_tag]}...")
        lemmas = collect_lemmas(morph, pos_tag, args.limit)
        print(f"  Found {len(lemmas)} lemmas.")

        pos_name = POS_MAP[pos_tag]
        for base_form, gender_name in lemmas:
            all_lemmas.append((base_form, pos_name, gender_name))

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["base_form", "part_of_speech_name", "gender_name"])
        for row in all_lemmas:
            writer.writerow(row)

    elapsed = time.time() - start
    file_size = _file_size_human(args.output)
    print(f"\nDone in {elapsed:.1f}s.")
    print(f"Wrote {len(all_lemmas)} words to {args.output} ({file_size})")


def _file_size_human(path):
    """Return human-readable file size."""
    import os

    size = os.path.getsize(path)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


if __name__ == "__main__":
    main()
