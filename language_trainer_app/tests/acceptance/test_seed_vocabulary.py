"""Acceptance tests for the flow: an operator seeds the vocabulary.

The operator runs `manage.py seed_vocabulary`. The command reads nouns and
adjectives from the real pymorphy3 dictionary and writes words and their forms.
The reference rows (genders, cases, numbers, parts of speech) come from the
migrations. The dictionary is pinned in `requirements.txt`, so the tests can
name the words that it gives first.
"""

import io
import re

import pymorphy3
import pytest
from django.core.management import call_command

from language_trainer_app.models.case import Case
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber

NOUN = "Существительное"
ADJECTIVE = "Прилагательное"
MASCULINE = "Мужской"
FEMININE = "Женский"
NEUTER = "Средний"
SINGULAR = "Единственное"
PLURAL = "Множественное"
CASES = [
    "Именительный",
    "Родительный",
    "Дательный",
    "Винительный",
    "Творительный",
    "Предложный",
]
PREPOSITIONAL = "Предложный"
ANIMATE = "Anim"
INANIMATE = "Inan"

FIRST_NOUNS = {
    "аба": (FEMININE, INANIMATE),
    "абажур": (MASCULINE, INANIMATE),
    "абажурчик": (MASCULINE, INANIMATE),
    "абаз": (MASCULINE, INANIMATE),
    "абазия": (FEMININE, INANIMATE),
    "абазин": (MASCULINE, ANIMATE),
}
FIRST_ADJECTIVES = [
    "аахенский",
    "абабковский",
    "абагайтуйский",
    "абагурский",
    "абадзехский",
    "абажурный",
]

LAMPSHADE_SINGULAR = ["абажур", "абажура", "абажуру", "абажур", "абажуром", "абажуре"]
LAMPSHADE_PLURAL = [
    "абажуры",
    "абажуров",
    "абажурам",
    "абажуры",
    "абажурами",
    "абажурах",
]
# "аба" (a cloth) has no plural in the dictionary.
ABA_SINGULAR = ["аба", "абы", "абе", "абу", "абой", "абе"]
# The dictionary gives the animate accusative ("-ого", "-их") for adjectives.
AACHEN = {
    MASCULINE: [
        "аахенский",
        "аахенского",
        "аахенскому",
        "аахенского",
        "аахенским",
        "аахенском",
    ],
    FEMININE: [
        "аахенская",
        "аахенской",
        "аахенской",
        "аахенскую",
        "аахенской",
        "аахенской",
    ],
    NEUTER: [
        "аахенское",
        "аахенского",
        "аахенскому",
        "аахенское",
        "аахенским",
        "аахенском",
    ],
    None: [
        "аахенские",
        "аахенских",
        "аахенским",
        "аахенских",
        "аахенскими",
        "аахенских",
    ],
}


def seed(*args):
    """Run the command as the operator does. Returns (stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    call_command("seed_vocabulary", *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def words_of(part_of_speech):
    """{base form: (gender name, animacy)} of the stored words, in insert order."""
    return {
        word.base_form: (word.gender.name if word.gender else None, word.animacy)
        for word in Word.objects.filter(part_of_speech__name=part_of_speech)
        .select_related("gender")
        .order_by("id")
    }


def forms_of(base_form, part_of_speech=NOUN):
    """{(case, number, form gender): form} of one stored word."""
    return {
        (
            form.case.name,
            form.number.name,
            form.gender.name if form.gender else None,
        ): form.word_form
        for form in WordForm.objects.filter(
            word__base_form=base_form, word__part_of_speech__name=part_of_speech
        ).select_related("case", "number", "gender")
    }


def noun_forms(singular, plural):
    forms = {}
    for number, words in ((SINGULAR, singular), (PLURAL, plural)):
        for case, word in zip(CASES, words):
            forms[(case, number, None)] = word
    return forms


def adjective_forms(by_gender):
    forms = {}
    for gender, words in by_gender.items():
        number = PLURAL if gender is None else SINGULAR
        for case, word in zip(CASES, words):
            forms[(case, number, gender)] = word
    return forms


def without(forms, case=None, number=None, gender=False):
    """The forms minus those of one case, one number or one form gender."""
    return {
        key: word
        for key, word in forms.items()
        if key[0] != case and key[1] != number and (gender is False or key[2] != gender)
    }


def output_lines(out):
    return [line.strip() for line in out.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Empty database
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_limit_seeds_the_first_nouns_and_adjectives_of_the_dictionary():
    out, err = seed("--limit", "6")

    assert err == ""
    assert words_of(NOUN) == FIRST_NOUNS
    assert words_of(ADJECTIVE) == {name: (MASCULINE, None) for name in FIRST_ADJECTIVES}
    assert forms_of("абажур") == noun_forms(LAMPSHADE_SINGULAR, LAMPSHADE_PLURAL)
    assert forms_of("аба") == noun_forms(ABA_SINGULAR, [])
    assert forms_of("аахенский", ADJECTIVE) == adjective_forms(AACHEN)
    noun_form_count = WordForm.objects.filter(word__part_of_speech__name=NOUN).count()
    adjective_form_count = WordForm.objects.filter(
        word__part_of_speech__name=ADJECTIVE
    ).count()
    assert adjective_form_count == 6 * 24
    *lines, last = output_lines(out)
    assert lines == [
        "Loading pymorphy2 dictionary...",
        "Dictionary loaded.",
        "=" * 60,
        f"Processing {NOUN} (NOUN)...",
        "=" * 60,
        "Collecting lemmas from dictionary...",
        "Found 6 lemmas.",
        "Creating Word objects...",
        "Created/found 6 words.",
        "Generating word forms...",
        f"Created {noun_form_count} word forms.",
        "=" * 60,
        f"Processing {ADJECTIVE} (ADJF)...",
        "=" * 60,
        "Collecting lemmas from dictionary...",
        "Found 6 lemmas.",
        "Creating Word objects...",
        "Created/found 6 words.",
        "Generating word forms...",
        f"Created {adjective_form_count} word forms.",
    ]
    assert re.fullmatch(
        rf"Done in \d+\.\ds\. Total: 12 words, "
        rf"{noun_form_count + adjective_form_count} word forms\.",
        last,
    )


@pytest.mark.django_db
def test_pos_noun_seeds_only_nouns():
    out, err = seed("--pos", "noun", "--limit", "3")

    assert err == ""
    assert list(words_of(NOUN)) == list(FIRST_NOUNS)[:3]
    assert words_of(ADJECTIVE) == {}
    assert "(NOUN)" in out
    assert "(ADJF)" not in out


@pytest.mark.django_db
def test_pos_adj_seeds_only_adjectives():
    out, err = seed("--pos", "adj", "--limit", "3")

    assert err == ""
    assert words_of(NOUN) == {}
    assert words_of(ADJECTIVE) == {
        name: (MASCULINE, None) for name in FIRST_ADJECTIVES[:3]
    }
    assert "(ADJF)" in out
    assert "(NOUN)" not in out


@pytest.mark.django_db
def test_thousands_of_nouns_are_written_in_batches_and_skip_unusable_words():
    out, err = seed("--pos", "noun", "--limit", "5000")

    assert err == ""
    assert Word.objects.count() == 5000
    lines = output_lines(out)
    assert [line for line in lines if line.startswith("...")] == [
        "... 1000 words created",
        "... 2000 words created",
        "... 3000 words created",
        "... 4000 words created",
        "... 5000 words created",
        "... processed 5000/5000 lemmas",
    ]
    assert f"Created {WordForm.objects.count()} word forms." in lines
    # Each of these is a noun in the dictionary, inside the first 5000 nouns.
    morph = pymorphy3.MorphAnalyzer()
    skipped = {
        "а-конто": "has a hyphen",
        "25-летие": "has digits",
        "б": "is one letter",
        "аарон": "is a name",
        "автовесы": "has no gender (plural only)",
    }
    for word in skipped:
        assert any(p.tag.POS == "NOUN" for p in morph.parse(word)), word
    stored = set(Word.objects.values_list("base_form", flat=True))
    assert {word: reason for word, reason in skipped.items() if word in stored} == {}


# ---------------------------------------------------------------------------
# Database with words
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_second_run_with_more_than_100_words_says_already_seeded():
    seed("--limit", "51")
    form_count = WordForm.objects.count()

    out, err = seed("--limit", "60")

    assert err == ""
    assert out == ("Vocabulary already seeded (102 words). Use --force to re-import.\n")
    assert Word.objects.count() == 102
    assert WordForm.objects.count() == form_count


@pytest.mark.django_db
def test_second_run_with_100_words_runs_again_and_adds_nothing():
    seed("--limit", "50")
    words = {pos: words_of(pos) for pos in (NOUN, ADJECTIVE)}
    form_count = WordForm.objects.count()

    out, err = seed("--limit", "50")

    assert err == ""
    assert "already seeded" not in out
    assert output_lines(out).count("Found 50 lemmas.") == 2
    assert output_lines(out).count("Created/found 50 words.") == 2
    assert {pos: words_of(pos) for pos in (NOUN, ADJECTIVE)} == words
    assert WordForm.objects.count() == form_count


@pytest.mark.django_db
def test_bigger_limit_adds_only_the_missing_words():
    seed("--limit", "2")
    first_rows = list(Word.objects.order_by("id").values_list("id", "base_form"))

    out, err = seed("--limit", "3")

    assert err == ""
    rows = list(Word.objects.order_by("id").values_list("id", "base_form"))
    assert rows[:4] == first_rows
    assert list(words_of(NOUN)) == list(FIRST_NOUNS)[:3]
    assert list(words_of(ADJECTIVE)) == FIRST_ADJECTIVES[:3]
    assert forms_of("абажурчик")[("Именительный", SINGULAR, None)] == "абажурчик"
    assert output_lines(out).count("Created/found 3 words.") == 2


@pytest.mark.django_db
def test_force_deletes_all_words_and_seeds_again():
    seed("--limit", "51")

    out, err = seed("--force", "--limit", "2")

    assert err == ""
    lines = output_lines(out)
    assert lines[2:4] == ["Deleting 102 existing words...", "Deleted."]
    assert list(words_of(NOUN)) == list(FIRST_NOUNS)[:2]
    assert list(words_of(ADJECTIVE)) == FIRST_ADJECTIVES[:2]
    assert not WordForm.objects.filter(word__base_form="абажурчик").exists()


@pytest.mark.django_db
def test_force_on_empty_database_has_nothing_to_delete():
    out, err = seed("--force", "--limit", "1")

    assert err == ""
    assert "Deleting" not in out
    assert Word.objects.count() == 2


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model, message",
    [
        (Gender, "No genders in DB. Run migrate first."),
        (Case, "No cases in DB. Run migrate first."),
        (WordNumber, "No word numbers in DB. Run migrate first."),
        (PartOfSpeech, "No parts of speech in DB. Run migrate first."),
    ],
)
def test_missing_reference_table_stops_before_any_word(model, message):
    model.objects.all().delete()

    out, err = seed("--limit", "1")

    assert err == message + "\n"
    assert out == ""
    assert Word.objects.count() == 0
    assert WordForm.objects.count() == 0


@pytest.mark.django_db
def test_renamed_part_of_speech_is_skipped_and_the_other_is_seeded():
    PartOfSpeech.objects.filter(name=ADJECTIVE).update(name="Adjective")

    out, err = seed("--limit", "2")

    assert err == f"PartOfSpeech '{ADJECTIVE}' not found in DB.\n"
    assert list(words_of(NOUN)) == list(FIRST_NOUNS)[:2]
    assert Word.objects.count() == 2
    assert "(ADJF)" not in out


@pytest.mark.django_db
def test_without_the_prepositional_case_no_form_has_it():
    Case.objects.filter(name=PREPOSITIONAL).delete()

    seed("--limit", "2")

    lampshade = noun_forms(LAMPSHADE_SINGULAR, LAMPSHADE_PLURAL)
    assert forms_of("абажур") == without(lampshade, case=PREPOSITIONAL)
    assert forms_of("аахенский", ADJECTIVE) == without(
        adjective_forms(AACHEN), case=PREPOSITIONAL
    )


@pytest.mark.django_db
def test_without_the_plural_only_singular_forms_are_seeded():
    WordNumber.objects.filter(name=PLURAL).delete()

    seed("--limit", "2")

    lampshade = noun_forms(LAMPSHADE_SINGULAR, LAMPSHADE_PLURAL)
    assert forms_of("абажур") == without(lampshade, number=PLURAL)
    assert forms_of("аахенский", ADJECTIVE) == without(
        adjective_forms(AACHEN), number=PLURAL
    )


@pytest.mark.django_db
def test_without_the_singular_only_plural_forms_are_seeded():
    WordNumber.objects.filter(name=SINGULAR).delete()

    seed("--limit", "2")

    lampshade = noun_forms(LAMPSHADE_SINGULAR, LAMPSHADE_PLURAL)
    assert forms_of("абажур") == without(lampshade, number=SINGULAR)
    assert forms_of("аба") == {}
    assert forms_of("аахенский", ADJECTIVE) == without(
        adjective_forms(AACHEN), number=SINGULAR
    )


@pytest.mark.django_db
def test_without_the_feminine_gender_feminine_words_get_no_gender_and_no_forms():
    Gender.objects.filter(name=FEMININE).delete()

    seed("--limit", "2")

    assert words_of(NOUN) == {
        "аба": (None, INANIMATE),
        "абажур": (MASCULINE, INANIMATE),
    }
    assert forms_of("аба") == {}
    assert forms_of("абажур") == noun_forms(LAMPSHADE_SINGULAR, LAMPSHADE_PLURAL)
    assert forms_of("аахенский", ADJECTIVE) == without(
        adjective_forms(AACHEN), gender=FEMININE
    )


@pytest.mark.django_db
def test_without_the_masculine_gender_adjectives_get_no_forms():
    Gender.objects.filter(name=MASCULINE).delete()

    out, err = seed("--pos", "adj", "--limit", "2")

    assert err == ""
    assert words_of(ADJECTIVE) == {name: (None, None) for name in FIRST_ADJECTIVES[:2]}
    assert WordForm.objects.count() == 0
    assert "Created 0 word forms." in output_lines(out)


# ---------------------------------------------------------------------------
# Rare dictionary entries
# ---------------------------------------------------------------------------

# Rare entries sit deep in the dictionary (noun 5910, adjectives 12391 and
# 32061). A run that reaches them takes minutes, and so does a run without
# --limit. This analyzer is the real one, but its word list holds only the real
# parses of a few words, in the order of the real dictionary.
SHORT_DICTIONARY = ["вагоновожатая", "вагоновожатый", "княжой", "саргассово"]


class ShortDictionaryAnalyzer(pymorphy3.MorphAnalyzer):
    def iter_known_word_parses(self, prefix=""):
        for word in SHORT_DICTIONARY:
            yield from self.parse(word)


@pytest.mark.django_db
def test_run_without_limit_takes_every_word_of_the_dictionary(monkeypatch):
    monkeypatch.setattr(pymorphy3, "MorphAnalyzer", ShortDictionaryAnalyzer)

    out, err = seed()

    assert err == ""
    lines = output_lines(out)
    assert lines.count("Found 1 lemmas.") == 1
    assert lines.count("Found 2 lemmas.") == 1
    # The dictionary gives "вагоновожатая" (feminine) first, with the base form
    # "вагоновожатый". No feminine parse of the base form exists, so the forms
    # come from the masculine parse.
    assert words_of(NOUN) == {"вагоновожатый": (FEMININE, ANIMATE)}
    assert forms_of("вагоновожатый") == noun_forms(
        [
            "вагоновожатый",
            "вагоновожатого",
            "вагоновожатому",
            "вагоновожатого",
            "вагоновожатым",
            "вагоновожатом",
        ],
        [
            "вагоновожатые",
            "вагоновожатых",
            "вагоновожатым",
            "вагоновожатых",
            "вагоновожатыми",
            "вагоновожатых",
        ],
    )
    assert words_of(ADJECTIVE) == {
        "княжой": (MASCULINE, None),
        "саргассово": (MASCULINE, None),
    }
    # "княжой" has no plural forms in the dictionary.
    assert forms_of("княжой", ADJECTIVE) == adjective_forms(
        {
            MASCULINE: ["княжой", "княжого", "княжому", "княжого", "княжим", "княжом"],
            FEMININE: ["княжая", "княжой", "княжой", "княжую", "княжой", "княжой"],
            NEUTER: ["княжое", "княжого", "княжому", "княжое", "княжим", "княжом"],
        }
    )
    # "саргассово" has only a neuter parse, so it has no masculine or feminine forms.
    assert forms_of("саргассово", ADJECTIVE) == adjective_forms(
        {
            NEUTER: [
                "саргассово",
                "саргассова",
                "саргассову",
                "саргассово",
                "саргассовым",
                "саргассовом",
            ],
            None: [
                "саргассовы",
                "саргассовых",
                "саргассовым",
                "саргассовы",
                "саргассовыми",
                "саргассовых",
            ],
        }
    )
