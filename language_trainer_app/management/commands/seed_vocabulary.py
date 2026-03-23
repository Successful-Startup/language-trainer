"""
Management command: seed_vocabulary

Populates the database with Russian nouns and adjectives (all declension forms)
using the pymorphy3 morphological dictionary (based on OpenCorpora / Zaliznyak).

Usage:
    python manage.py seed_vocabulary              # full dictionary, skip if exists
    python manage.py seed_vocabulary --force       # drop existing & re-seed
    python manage.py seed_vocabulary --limit 1000  # only first N lemmas per POS
    python manage.py seed_vocabulary --pos noun    # only nouns
    python manage.py seed_vocabulary --pos adj     # only adjectives
"""

import re
import time

import pymorphy3
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from language_trainer_app.models import (
    Case,
    Gender,
    PartOfSpeech,
    Word,
    WordForm,
    WordNumber,
)

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

# Words containing these characters are skipped (abbreviations, hyphenated, etc.)
SKIP_RE = re.compile(r"[-\d./]")

# pymorphy3 tags that mark proper nouns (names, surnames, patronymics, etc.)
PROPER_NOUN_TAGS = {"Name", "Surn", "Patr", "Geox", "Orgn"}

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Seed the database with Russian nouns and adjectives from pymorphy3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing seeded words and re-import",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of lemmas per part of speech (0 = no limit)",
        )
        parser.add_argument(
            "--pos",
            choices=["noun", "adj", "both"],
            default="both",
            help="Which parts of speech to seed (default: both)",
        )

    def handle(self, *args, **options):
        force = options["force"]
        limit = options["limit"]
        pos_filter = options["pos"]

        # ── Check if already seeded ────────────────────────────────────
        existing_words = Word.objects.count()
        if existing_words > 100 and not force:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Vocabulary already seeded ({existing_words} words). "
                    f"Use --force to re-import."
                )
            )
            return

        # ── Load reference data from DB ────────────────────────────────
        ref = self._load_reference_data()
        if ref is None:
            return

        # ── Initialize pymorphy2 ───────────────────────────────────────
        self.stdout.write("Loading pymorphy2 dictionary...")
        morph = pymorphy3.MorphAnalyzer()
        self.stdout.write(self.style.SUCCESS("Dictionary loaded."))

        # ── Determine which POS tags to process ────────────────────────
        pos_tags = []
        if pos_filter in ("noun", "both"):
            pos_tags.append("NOUN")
        if pos_filter in ("adj", "both"):
            pos_tags.append("ADJF")

        # ── If --force, delete existing words (cascades to word forms) ─
        if force and existing_words > 0:
            self.stdout.write(f"Deleting {existing_words} existing words...")
            Word.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Deleted."))

        # ── Collect lemmas from pymorphy2 dictionary ───────────────────
        start_time = time.time()

        for pos_tag in pos_tags:
            self._seed_pos(morph, pos_tag, limit, ref)

        elapsed = time.time() - start_time
        total_words = Word.objects.count()
        total_forms = WordForm.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone in {elapsed:.1f}s. "
                f"Total: {total_words} words, {total_forms} word forms."
            )
        )

    # ── Reference data loader ──────────────────────────────────────────

    def _load_reference_data(self):
        """Load Gender, Case, WordNumber, PartOfSpeech from DB into dicts."""
        ref = {}

        # Genders
        ref["genders"] = {}
        for g in Gender.objects.all():
            ref["genders"][g.name] = g
        if not ref["genders"]:
            self.stderr.write(self.style.ERROR("No genders in DB. Run migrate first."))
            return None

        # Cases
        ref["cases"] = {}
        for c in Case.objects.all():
            ref["cases"][c.name] = c
        if not ref["cases"]:
            self.stderr.write(self.style.ERROR("No cases in DB. Run migrate first."))
            return None

        # Word numbers
        ref["numbers"] = {}
        for n in WordNumber.objects.all():
            ref["numbers"][n.name] = n
        if not ref["numbers"]:
            self.stderr.write(
                self.style.ERROR("No word numbers in DB. Run migrate first.")
            )
            return None

        # Parts of speech
        ref["pos"] = {}
        for p in PartOfSpeech.objects.all():
            ref["pos"][p.name] = p
        if not ref["pos"]:
            self.stderr.write(
                self.style.ERROR("No parts of speech in DB. Run migrate first.")
            )
            return None

        return ref

    # ── Per-POS seeding logic ──────────────────────────────────────────

    def _seed_pos(self, morph, pos_tag, limit, ref):
        """Seed words and word forms for a single POS tag (NOUN or ADJF)."""
        pos_name = POS_MAP[pos_tag]
        pos_obj = ref["pos"].get(pos_name)
        if pos_obj is None:
            self.stderr.write(
                self.style.ERROR(f"PartOfSpeech '{pos_name}' not found in DB.")
            )
            return

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Processing {pos_name} ({pos_tag})...")
        self.stdout.write(f"{'='*60}")

        # ── Step 1: Collect lemmas ─────────────────────────────────────
        self.stdout.write("Collecting lemmas from dictionary...")
        lemmas = self._collect_lemmas(morph, pos_tag, limit)
        self.stdout.write(f"  Found {len(lemmas)} lemmas.")

        # ── Step 2: Bulk-create Word objects ───────────────────────────
        self.stdout.write("Creating Word objects...")
        word_map = self._bulk_create_words(lemmas, pos_tag, pos_obj, ref)
        self.stdout.write(f"  Created/found {len(word_map)} words.")

        # ── Step 3: Generate and bulk-create WordForm objects ──────────
        self.stdout.write("Generating word forms...")
        forms_created = self._bulk_create_word_forms(
            morph, lemmas, pos_tag, word_map, ref
        )
        self.stdout.write(f"  Created {forms_created} word forms.")

    # ── Lemma collection ───────────────────────────────────────────────

    def _collect_lemmas(self, morph, pos_tag, limit):
        """
        Iterate over the pymorphy3 dictionary and collect lemmas for a given POS.

        Returns a list of (normal_form, gender_tag_or_None) tuples.
        """
        seen = set()
        lemmas = []

        for word_obj in morph.iter_known_word_parses():
            if limit and len(lemmas) >= limit:
                break

            # Only consider the lexeme's normal form
            tag = word_obj.tag
            if tag.POS != pos_tag:
                continue

            normal = word_obj.normal_form
            if normal in seen:
                continue
            if SKIP_RE.search(normal):
                continue
            # Skip single-character or very short words
            if len(normal) < 2:
                continue
            # Skip proper nouns (names, surnames, patronymics, places, orgs)
            tag_str = str(tag)
            if any(t in tag_str for t in PROPER_NOUN_TAGS):
                continue

            # Determine gender
            gender_tag = str(tag.gender) if tag.gender else None

            # For nouns: must have a gender
            if pos_tag == "NOUN" and gender_tag not in GENDER_MAP:
                continue

            # For adjectives: store as masculine (base dictionary form)
            if pos_tag == "ADJF":
                gender_tag = "masc"

            seen.add(normal)
            lemmas.append((normal, gender_tag))

        return lemmas

    # ── Bulk Word creation ─────────────────────────────────────────────

    def _bulk_create_words(self, lemmas, pos_tag, pos_obj, ref):
        """
        Create Word objects in bulk. Returns a dict mapping
        (base_form, gender_name) → Word instance.
        """
        word_map = {}

        # First, fetch existing words to avoid duplicates
        existing = set(
            Word.objects.filter(part_of_speech=pos_obj).values_list(
                "base_form", flat=True
            )
        )

        batch = []
        count = 0

        for normal_form, gender_tag in lemmas:
            base_form = normal_form.lower()
            if base_form in existing:
                continue

            gender_name = GENDER_MAP.get(gender_tag)
            gender_obj = ref["genders"].get(gender_name) if gender_name else None

            word = Word(
                base_form=base_form,
                part_of_speech=pos_obj,
                gender=gender_obj,
            )
            batch.append(word)
            count += 1

            if len(batch) >= BATCH_SIZE:
                self._flush_words(batch)
                self.stdout.write(f"    ... {count} words created")
                batch = []

        if batch:
            self._flush_words(batch)

        # Now load all words back to get their PKs
        for w in Word.objects.filter(part_of_speech=pos_obj).select_related("gender"):
            gender_name = w.gender.name if w.gender else None
            word_map[(w.base_form, gender_name)] = w

        return word_map

    def _flush_words(self, batch):
        """Insert a batch of Word objects, ignoring conflicts."""
        with transaction.atomic():
            Word.objects.bulk_create(batch, ignore_conflicts=True)

    # ── Bulk WordForm creation ─────────────────────────────────────────

    def _bulk_create_word_forms(self, morph, lemmas, pos_tag, word_map, ref):
        """Generate all declension forms and bulk-insert them."""
        batch = []
        total_created = 0

        for idx, (normal_form, gender_tag) in enumerate(lemmas):
            base_form = normal_form.lower()
            gender_name = GENDER_MAP.get(gender_tag)
            word_obj = word_map.get((base_form, gender_name))

            if word_obj is None:
                continue

            # Get the correct parse for this word
            parse = self._get_best_parse(morph, normal_form, pos_tag, gender_tag)
            if parse is None:
                continue

            if pos_tag == "NOUN":
                forms = self._inflect_noun(parse, word_obj, ref)
            else:
                forms = self._inflect_adjective(parse, word_obj, ref)

            batch.extend(forms)

            if len(batch) >= BATCH_SIZE:
                total_created += self._flush_word_forms(batch)
                batch = []

            if (idx + 1) % 5000 == 0:
                self.stdout.write(f"    ... processed {idx + 1}/{len(lemmas)} lemmas")

        if batch:
            total_created += self._flush_word_forms(batch)

        return total_created

    def _flush_word_forms(self, batch):
        """Insert a batch of WordForm objects, ignoring conflicts."""
        with transaction.atomic():
            created = WordForm.objects.bulk_create(batch, ignore_conflicts=True)
        count = len(created)
        return count

    def _get_best_parse(self, morph, word, target_pos, target_gender):
        """Find the pymorphy2 parse that matches the expected POS and gender."""
        parses = morph.parse(word)
        for p in parses:
            if str(p.tag.POS) == target_pos:
                if target_gender and str(p.tag.gender) == target_gender:
                    return p
                if not target_gender:
                    return p
        # Fallback: return first parse with matching POS
        for p in parses:
            if str(p.tag.POS) == target_pos:
                return p
        return None

    # ── Noun inflection ────────────────────────────────────────────────

    def _inflect_noun(self, parse, word_obj, ref):
        """Generate 6 cases x 2 numbers = 12 forms for a noun."""
        forms = []
        for case_tag, case_name in CASE_MAP.items():
            case_obj = ref["cases"].get(case_name)
            if case_obj is None:
                continue

            for num_tag, num_name in NUMBER_MAP.items():
                num_obj = ref["numbers"].get(num_name)
                if num_obj is None:
                    continue

                inflected = parse.inflect({case_tag, num_tag})
                if inflected is None:
                    continue

                form = WordForm(
                    word=word_obj,
                    case=case_obj,
                    gender=None,  # nouns don't have form-level gender
                    number=num_obj,
                    word_form=inflected.word.lower(),
                )
                forms.append(form)

        return forms

    # ── Adjective inflection ───────────────────────────────────────────

    def _inflect_adjective(self, parse, word_obj, ref):
        """
        Generate forms for an adjective (full forms only — ADJF).
        Singular: 6 cases x 3 genders = 18 forms (form_gender filled).
        Plural:   6 cases x 1 = 6 forms (form_gender = None, gender not
                  distinguished in plural).
        Total: up to 24 forms per adjective.
        """
        forms = []

        # ── Singular: iterate over genders ─────────────────────────────
        for gender_tag, gender_name in GENDER_MAP.items():
            gender_obj = ref["genders"].get(gender_name)
            if gender_obj is None:
                continue

            num_obj = ref["numbers"].get("Единственное")
            if num_obj is None:
                continue

            for case_tag, case_name in CASE_MAP.items():
                case_obj = ref["cases"].get(case_name)
                if case_obj is None:
                    continue

                inflected = parse.inflect({"ADJF", case_tag, gender_tag, "sing"})
                if inflected is None:
                    continue

                form = WordForm(
                    word=word_obj,
                    case=case_obj,
                    gender=gender_obj,  # form-level gender for adjectives
                    number=num_obj,
                    word_form=inflected.word.lower(),
                )
                forms.append(form)

        # ── Plural: no gender distinction ──────────────────────────────
        num_obj = ref["numbers"].get("Множественное")
        if num_obj is not None:
            for case_tag, case_name in CASE_MAP.items():
                case_obj = ref["cases"].get(case_name)
                if case_obj is None:
                    continue

                inflected = parse.inflect({"ADJF", case_tag, "plur"})
                if inflected is None:
                    continue

                form = WordForm(
                    word=word_obj,
                    case=case_obj,
                    gender=None,  # no gender in plural
                    number=num_obj,
                    word_form=inflected.word.lower(),
                )
                forms.append(form)

        return forms
