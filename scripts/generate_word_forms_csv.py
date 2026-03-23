#!/usr/bin/env python3
"""
Generate a word_forms CSV file from a words CSV using pymorphy2 inflection.

Reads the words CSV produced by generate_words_csv.py (or any CSV with columns
base_form, part_of_speech_name, gender_name), inflects each word through all
cases and numbers, and writes the result in the format expected by the
Language Trainer word-forms import endpoint.

Output format (word_forms.csv):
    word_base_form,word_part_of_speech_name,word_gender_name,word_form,case_name,form_gender_name,number_name
    стол,Существительное,Мужской,стол,Именительный,,Единственное
    стол,Существительное,Мужской,стола,Родительный,,Единственное
    ...
    большой,Прилагательное,Мужской,большого,Родительный,Мужской,Единственное

Usage:
    python generate_word_forms_csv.py                              # default I/O
    python generate_word_forms_csv.py -i words.csv -o forms.csv    # custom paths

Requirements:
    pip install pymorphy3
"""

import argparse
import csv
import sys
import time

import pymorphy3

# ── Reverse mapping: DB name → pymorphy2 tag ──────────────────────────────

POS_REVERSE = {
    "Существительное": "NOUN",
    "Прилагательное": "ADJF",
}

GENDER_REVERSE = {
    "Мужской": "masc",
    "Женский": "femn",
    "Средний": "neut",
}

CASE_MAP = {
    "nomn": "Именительный",
    "gent": "Родительный",
    "datv": "Дательный",
    "accs": "Винительный",
    "ablt": "Творительный",
    "loct": "Предложный",
}

NUMBER_MAP = {
    "sing": "Единственное",
    "plur": "Множественное",
}

GENDER_MAP = {
    "masc": "Мужской",
    "femn": "Женский",
    "neut": "Средний",
}


def get_best_parse(morph, word, target_pos, target_gender_tag):
    """Find pymorphy2 parse matching expected POS and gender."""
    parses = morph.parse(word)
    for p in parses:
        if str(p.tag.POS) == target_pos:
            if target_gender_tag and str(p.tag.gender) == target_gender_tag:
                return p
            if not target_gender_tag:
                return p
    for p in parses:
        if str(p.tag.POS) == target_pos:
            return p
    return None


def inflect_noun(parse, word_row):
    """Generate 6 cases x 2 numbers = 12 forms for a noun."""
    rows = []
    for case_tag, case_name in CASE_MAP.items():
        for num_tag, num_name in NUMBER_MAP.items():
            inflected = parse.inflect({case_tag, num_tag})
            if inflected is None:
                continue
            rows.append(
                {
                    "word_base_form": word_row["base_form"],
                    "word_part_of_speech_name": word_row["part_of_speech_name"],
                    "word_gender_name": word_row["gender_name"],
                    "word_form": inflected.word.lower(),
                    "case_name": case_name,
                    "form_gender_name": "",
                    "number_name": num_name,
                }
            )
    return rows


def inflect_adjective(parse, word_row):
    """
    Generate forms for a full adjective (ADJF).
    Singular: 6 cases x 3 genders = 18 forms.
    Plural:   6 cases = 6 forms (no gender).
    Total: up to 24 forms.
    """
    rows = []

    # Singular — iterate over genders
    for gender_tag, gender_name in GENDER_MAP.items():
        for case_tag, case_name in CASE_MAP.items():
            inflected = parse.inflect({"ADJF", case_tag, gender_tag, "sing"})
            if inflected is None:
                continue
            rows.append(
                {
                    "word_base_form": word_row["base_form"],
                    "word_part_of_speech_name": word_row["part_of_speech_name"],
                    "word_gender_name": word_row["gender_name"],
                    "word_form": inflected.word.lower(),
                    "case_name": case_name,
                    "form_gender_name": gender_name,
                    "number_name": "Единственное",
                }
            )

    # Plural — no gender distinction
    for case_tag, case_name in CASE_MAP.items():
        inflected = parse.inflect({"ADJF", case_tag, "plur"})
        if inflected is None:
            continue
        rows.append(
            {
                "word_base_form": word_row["base_form"],
                "word_part_of_speech_name": word_row["part_of_speech_name"],
                "word_gender_name": word_row["gender_name"],
                "word_form": inflected.word.lower(),
                "case_name": case_name,
                "form_gender_name": "",
                "number_name": "Множественное",
            }
        )

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Generate word forms CSV from a words CSV using pymorphy2"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="words.csv",
        help="Input words CSV (default: words.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="word_forms.csv",
        help="Output word forms CSV (default: word_forms.csv)",
    )
    args = parser.parse_args()

    # Read input words
    print(f"Reading words from {args.input}...")
    words = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(row)
    print(f"  Read {len(words)} words.")

    print("Loading pymorphy2 dictionary...")
    morph = pymorphy3.MorphAnalyzer()
    print("Dictionary loaded.")

    fieldnames = [
        "word_base_form",
        "word_part_of_speech_name",
        "word_gender_name",
        "word_form",
        "case_name",
        "form_gender_name",
        "number_name",
    ]

    start = time.time()
    total_forms = 0
    skipped = 0

    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, word_row in enumerate(words):
            pos_name = word_row["part_of_speech_name"]
            pos_tag = POS_REVERSE.get(pos_name)
            if pos_tag is None:
                skipped += 1
                continue

            gender_name = word_row.get("gender_name", "")
            gender_tag = GENDER_REVERSE.get(gender_name)

            parse = get_best_parse(morph, word_row["base_form"], pos_tag, gender_tag)
            if parse is None:
                skipped += 1
                continue

            if pos_tag == "NOUN":
                form_rows = inflect_noun(parse, word_row)
            else:
                form_rows = inflect_adjective(parse, word_row)

            writer.writerows(form_rows)
            total_forms += len(form_rows)

            if (idx + 1) % 5000 == 0:
                print(f"  ... processed {idx + 1}/{len(words)} words")

    elapsed = time.time() - start
    file_size = _file_size_human(args.output)
    print(f"\nDone in {elapsed:.1f}s.")
    print(f"Wrote {total_forms} word forms to {args.output} ({file_size})")
    if skipped:
        print(f"Skipped {skipped} words (unknown POS or could not parse).")


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
