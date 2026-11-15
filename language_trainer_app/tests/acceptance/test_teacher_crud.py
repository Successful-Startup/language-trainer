"""Acceptance tests for the flow: a teacher manages the data.

The teacher logs in with a password and sends the JWT, as the frontend does.
Anyone can read the data, but only a logged-in user can change it.
"""

import pytest

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber

UNKNOWN_ID = 999999
NOT_LOGGED_IN = {"detail": "Authentication credentials were not provided."}
REQUIRED = ["This field is required."]

WORDS_URL = "/words/"
WORD_FORMS_URL = "/word-forms/"
CONTEXTS_URL = "/contexts/"
PAIRS_URL = "/context-word-form-pairs/"


def invalid_pk(pk=UNKNOWN_ID):
    return [f'Invalid pk "{pk}" - object does not exist.']


def detail_url(url, pk):
    return f"{url}{pk}/"


def rows_of(response):
    data = response.json()
    return data["results"] if isinstance(data, dict) else data


def word_body(word):
    return {
        "id": word.id,
        "base_form": word.base_form,
        "gender": word.gender_id,
        "part_of_speech": word.part_of_speech_id,
        "animacy": word.animacy,
    }


def word_form_body(form):
    return {
        "id": form.id,
        "word": word_body(form.word),
        "case": form.case_id,
        "gender": form.gender_id,
        "number": form.number_id,
        "word_form": form.word_form,
    }


def pair_body(pair):
    return {
        "id": pair.id,
        "context": {"id": pair.context.id, "text": pair.context.text},
        "noun_form": word_form_body(pair.noun_form),
        "adjective_form": (
            word_form_body(pair.adjective_form) if pair.adjective_form else None
        ),
    }


@pytest.fixture
def vocabulary(reference_data):
    """A noun and an adjective with one genitive form each, and a context."""
    rd = reference_data
    noun = Word.objects.create(
        base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
    )
    adjective = Word.objects.create(base_form="синий", part_of_speech=rd["pos_adj"])
    noun_form = WordForm.objects.create(
        word=noun, case=rd["case_gen"], number=rd["number_sg"], word_form="дома"
    )
    adjective_form = WordForm.objects.create(
        word=adjective,
        case=rd["case_gen"],
        gender=rd["gender_m"],
        number=rd["number_sg"],
        word_form="синего",
    )
    context = Context.objects.create(text="у ____")
    return {
        **rd,
        "noun": noun,
        "adjective": adjective,
        "noun_form": noun_form,
        "adjective_form": adjective_form,
        "context": context,
    }


# ---------------------------------------------------------------------------
# Every resource: anonymous read, anonymous write
# ---------------------------------------------------------------------------


@pytest.fixture
def one_of_each(vocabulary):
    """For each resource: its model, one saved row and a valid body for a write."""
    v = vocabulary
    pair = ContextWordFormPair.objects.create(
        context=v["context"], noun_form=v["noun_form"]
    )
    name_body = {"name": "звательный", "name_en": "Vocative"}
    return {
        "/genders/": (Gender, v["gender_m"], name_body),
        "/cases/": (Case, v["case_gen"], name_body),
        "/parts-of-speech/": (PartOfSpeech, v["pos_noun"], name_body),
        "/word-numbers/": (WordNumber, v["number_sg"], name_body),
        WORDS_URL: (
            Word,
            v["noun"],
            {"base_form": "кот", "part_of_speech": v["pos_noun"].id, "gender": None},
        ),
        WORD_FORMS_URL: (
            WordForm,
            v["noun_form"],
            {
                "word_id": v["noun"].id,
                "case": v["case_dat"].id,
                "gender": None,
                "number": v["number_sg"].id,
                "word_form": "дому",
            },
        ),
        CONTEXTS_URL: (Context, v["context"], {"text": "без ____"}),
        PAIRS_URL: (
            ContextWordFormPair,
            pair,
            {
                "context_id": v["context"].id,
                "noun_form_id": v["noun_form"].id,
                "adjective_form_id": v["adjective_form"].id,
            },
        ),
    }


ALL_URLS = [
    "/genders/",
    "/cases/",
    "/parts-of-speech/",
    "/word-numbers/",
    WORDS_URL,
    WORD_FORMS_URL,
    CONTEXTS_URL,
    PAIRS_URL,
]


@pytest.mark.parametrize("url", ALL_URLS)
def test_anonymous_user_reads_list_and_row(api_client, one_of_each, url):
    _, row, _ = one_of_each[url]

    listed = api_client.get(url)
    one = api_client.get(detail_url(url, row.id))

    assert listed.status_code == 200
    assert one.status_code == 200
    assert one.json()["id"] == row.id
    assert one.json() in rows_of(listed)


@pytest.mark.parametrize("url", ALL_URLS)
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_anonymous_user_cannot_write(api_client, one_of_each, url, method):
    model, row, body = one_of_each[url]
    before = list(model.objects.order_by("id").values())
    target = url if method == "post" else detail_url(url, row.id)

    response = getattr(api_client, method)(target, body, format="json")

    assert response.status_code == 401
    assert response.json() == NOT_LOGGED_IN
    assert list(model.objects.order_by("id").values()) == before


# ---------------------------------------------------------------------------
# Genders, cases, parts of speech, word numbers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url, model, verbose_name",
    [
        ("/genders/", Gender, "Род"),
        ("/cases/", Case, "Падеж"),
        ("/parts-of-speech/", PartOfSpeech, "Часть речи"),
        ("/word-numbers/", WordNumber, "Число"),
    ],
)
class TestNamedReferenceData:
    def test_teacher_creates_a_row(self, auth_client, db, url, model, verbose_name):
        response = auth_client.post(
            url, {"name": "звательный", "name_en": "Vocative"}, format="json"
        )

        assert response.status_code == 201
        row = model.objects.get(name="звательный")
        assert response.json() == {
            "id": row.id,
            "name": "звательный",
            "name_en": "Vocative",
        }
        assert row.name_en == "Vocative"

    def test_name_en_is_optional(self, auth_client, db, url, model, verbose_name):
        response = auth_client.post(url, {"name": "звательный"}, format="json")

        assert response.status_code == 201
        assert response.json()["name_en"] == ""
        assert model.objects.get(name="звательный").name_en == ""

    def test_anonymous_user_reads_the_row(
        self, api_client, db, url, model, verbose_name
    ):
        row = model.objects.create(name="звательный", name_en="Vocative")

        response = api_client.get(detail_url(url, row.id))

        assert response.status_code == 200
        assert response.json() == {
            "id": row.id,
            "name": "звательный",
            "name_en": "Vocative",
        }

    def test_list_holds_new_row_and_seeded_rows(
        self, api_client, db, url, model, verbose_name
    ):
        row = model.objects.create(name="звательный", name_en="Vocative")

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.json()["count"] == model.objects.count()
        assert {
            "id": row.id,
            "name": "звательный",
            "name_en": "Vocative",
        } in response.json()["results"]

    def test_teacher_replaces_a_row(self, auth_client, db, url, model, verbose_name):
        row = model.objects.create(name="звательный", name_en="")

        response = auth_client.put(
            detail_url(url, row.id),
            {"name": "местный", "name_en": "Locative"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": row.id,
            "name": "местный",
            "name_en": "Locative",
        }
        row.refresh_from_db()
        assert (row.name, row.name_en) == ("местный", "Locative")

    def test_teacher_changes_one_field(self, auth_client, db, url, model, verbose_name):
        row = model.objects.create(name="звательный", name_en="")

        response = auth_client.patch(
            detail_url(url, row.id), {"name_en": "Vocative"}, format="json"
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": row.id,
            "name": "звательный",
            "name_en": "Vocative",
        }
        row.refresh_from_db()
        assert (row.name, row.name_en) == ("звательный", "Vocative")

    def test_teacher_deletes_a_row(self, auth_client, db, url, model, verbose_name):
        row = model.objects.create(name="звательный")

        response = auth_client.delete(detail_url(url, row.id))

        assert response.status_code == 204
        assert not model.objects.filter(id=row.id).exists()
        assert auth_client.get(detail_url(url, row.id)).status_code == 404

    def test_duplicate_name_is_rejected(
        self, auth_client, db, url, model, verbose_name
    ):
        model.objects.create(name="звательный")
        count = model.objects.count()

        response = auth_client.post(url, {"name": "звательный"}, format="json")

        assert response.status_code == 400
        assert response.json() == {
            "name": [f"{verbose_name} with this name already exists."]
        }
        assert model.objects.count() == count

    def test_rename_to_existing_name_is_rejected(
        self, auth_client, db, url, model, verbose_name
    ):
        model.objects.create(name="звательный")
        row = model.objects.create(name="местный")

        response = auth_client.patch(
            detail_url(url, row.id), {"name": "звательный"}, format="json"
        )

        assert response.status_code == 400
        assert response.json() == {
            "name": [f"{verbose_name} with this name already exists."]
        }
        row.refresh_from_db()
        assert row.name == "местный"

    def test_name_is_required(self, auth_client, db, url, model, verbose_name):
        count = model.objects.count()

        response = auth_client.post(url, {"name_en": "Vocative"}, format="json")

        assert response.status_code == 400
        assert response.json() == {"name": REQUIRED}
        assert model.objects.count() == count


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------


class TestWords:
    def test_teacher_creates_a_noun(self, auth_client, reference_data):
        rd = reference_data

        response = auth_client.post(
            WORDS_URL,
            {
                "base_form": "кот",
                "part_of_speech": rd["pos_noun"].id,
                "gender": rd["gender_m"].id,
                "animacy": "Anim",
            },
            format="json",
        )

        assert response.status_code == 201
        word = Word.objects.get(base_form="кот")
        assert response.json() == {
            "id": word.id,
            "base_form": "кот",
            "gender": rd["gender_m"].id,
            "part_of_speech": rd["pos_noun"].id,
            "animacy": "Anim",
        }
        assert (word.part_of_speech, word.gender, word.animacy) == (
            rd["pos_noun"],
            rd["gender_m"],
            "Anim",
        )

    def test_gender_and_animacy_are_optional(self, auth_client, reference_data):
        response = auth_client.post(
            WORDS_URL,
            {"base_form": "синий", "part_of_speech": reference_data["pos_adj"].id},
            format="json",
        )

        assert response.status_code == 201
        word = Word.objects.get(base_form="синий")
        assert response.json() == word_body(word)
        assert (word.gender, word.animacy) == (None, None)

    def test_anonymous_user_reads_a_word(self, api_client, vocabulary):
        response = api_client.get(detail_url(WORDS_URL, vocabulary["noun"].id))

        assert response.status_code == 200
        assert response.json() == {
            "id": vocabulary["noun"].id,
            "base_form": "дом",
            "gender": vocabulary["gender_m"].id,
            "part_of_speech": vocabulary["pos_noun"].id,
            "animacy": None,
        }

    def test_teacher_replaces_a_word(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.put(
            detail_url(WORDS_URL, v["noun"].id),
            {
                "base_form": "доска",
                "part_of_speech": v["pos_noun"].id,
                "gender": v["gender_f"].id,
                "animacy": "Inan",
            },
            format="json",
        )

        assert response.status_code == 200
        v["noun"].refresh_from_db()
        assert response.json() == word_body(v["noun"])
        assert (v["noun"].base_form, v["noun"].gender, v["noun"].animacy) == (
            "доска",
            v["gender_f"],
            "Inan",
        )

    def test_teacher_changes_animacy_only(self, auth_client, vocabulary):
        noun = vocabulary["noun"]

        response = auth_client.patch(
            detail_url(WORDS_URL, noun.id), {"animacy": "Inan"}, format="json"
        )

        assert response.status_code == 200
        noun.refresh_from_db()
        assert response.json() == word_body(noun)
        assert (noun.base_form, noun.animacy) == ("дом", "Inan")

    def test_deleting_a_word_deletes_its_forms_and_pairs(self, auth_client, vocabulary):
        v = vocabulary
        ContextWordFormPair.objects.create(
            context=v["context"], noun_form=v["noun_form"]
        )

        response = auth_client.delete(detail_url(WORDS_URL, v["noun"].id))

        assert response.status_code == 204
        assert not Word.objects.filter(id=v["noun"].id).exists()
        assert not WordForm.objects.filter(id=v["noun_form"].id).exists()
        assert not ContextWordFormPair.objects.exists()
        assert Context.objects.filter(id=v["context"].id).exists()

    def test_unknown_animacy_is_rejected(self, auth_client, reference_data):
        response = auth_client.post(
            WORDS_URL,
            {
                "base_form": "кот",
                "part_of_speech": reference_data["pos_noun"].id,
                "animacy": "Alive",
            },
            format="json",
        )

        assert response.status_code == 400
        assert response.json() == {"animacy": ['"Alive" is not a valid choice.']}
        assert not Word.objects.filter(base_form="кот").exists()

    def test_base_form_and_part_of_speech_are_required(self, auth_client, db):
        response = auth_client.post(WORDS_URL, {}, format="json")

        assert response.status_code == 400
        assert response.json() == {"base_form": REQUIRED, "part_of_speech": REQUIRED}

    def test_unknown_part_of_speech_is_rejected(self, auth_client, db):
        response = auth_client.post(
            WORDS_URL,
            {"base_form": "кот", "part_of_speech": UNKNOWN_ID},
            format="json",
        )

        assert response.status_code == 400
        assert response.json() == {"part_of_speech": invalid_pk()}


# ---------------------------------------------------------------------------
# Word forms
# ---------------------------------------------------------------------------


class TestWordForms:
    def test_teacher_creates_a_form(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.post(
            WORD_FORMS_URL,
            {
                "word_id": v["adjective"].id,
                "case": v["case_dat"].id,
                "gender": v["gender_f"].id,
                "number": v["number_sg"].id,
                "word_form": "синей",
            },
            format="json",
        )

        assert response.status_code == 201
        form = WordForm.objects.get(word_form="синей")
        assert response.json() == {
            "id": form.id,
            "word": {
                "id": v["adjective"].id,
                "base_form": "синий",
                "gender": None,
                "part_of_speech": v["pos_adj"].id,
                "animacy": None,
            },
            "case": v["case_dat"].id,
            "gender": v["gender_f"].id,
            "number": v["number_sg"].id,
            "word_form": "синей",
        }
        assert (form.word, form.case, form.gender, form.number) == (
            v["adjective"],
            v["case_dat"],
            v["gender_f"],
            v["number_sg"],
        )

    def test_form_gender_is_optional(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.post(
            WORD_FORMS_URL,
            {
                "word_id": v["noun"].id,
                "case": v["case_dat"].id,
                "number": v["number_sg"].id,
                "word_form": "дому",
            },
            format="json",
        )

        assert response.status_code == 201
        form = WordForm.objects.get(word_form="дому")
        assert response.json() == word_form_body(form)
        assert form.gender is None

    def test_anonymous_user_reads_a_form(self, api_client, vocabulary):
        form = vocabulary["noun_form"]

        response = api_client.get(detail_url(WORD_FORMS_URL, form.id))

        assert response.status_code == 200
        assert response.json() == word_form_body(form)

    def test_teacher_replaces_a_form(self, auth_client, vocabulary):
        v = vocabulary
        form = v["noun_form"]

        response = auth_client.put(
            detail_url(WORD_FORMS_URL, form.id),
            {
                "word_id": v["noun"].id,
                "case": v["case_dat"].id,
                "gender": None,
                "number": v["number_sg"].id,
                "word_form": "дому",
            },
            format="json",
        )

        assert response.status_code == 200
        form.refresh_from_db()
        assert response.json() == word_form_body(form)
        assert (form.case, form.word_form) == (v["case_dat"], "дому")

    def test_teacher_changes_the_spelling_only(self, auth_client, vocabulary):
        form = vocabulary["noun_form"]

        response = auth_client.patch(
            detail_url(WORD_FORMS_URL, form.id), {"word_form": "дому"}, format="json"
        )

        assert response.status_code == 200
        form.refresh_from_db()
        assert response.json() == word_form_body(form)
        assert (form.case, form.word_form) == (vocabulary["case_gen"], "дому")

    def test_deleting_a_noun_form_deletes_its_pairs(self, auth_client, vocabulary):
        v = vocabulary
        ContextWordFormPair.objects.create(
            context=v["context"], noun_form=v["noun_form"]
        )

        response = auth_client.delete(detail_url(WORD_FORMS_URL, v["noun_form"].id))

        assert response.status_code == 204
        assert not WordForm.objects.filter(id=v["noun_form"].id).exists()
        assert not ContextWordFormPair.objects.exists()
        assert Word.objects.filter(id=v["noun"].id).exists()

    def test_deleting_an_adjective_form_keeps_the_pair_without_it(
        self, auth_client, vocabulary
    ):
        v = vocabulary
        pair = ContextWordFormPair.objects.create(
            context=v["context"],
            noun_form=v["noun_form"],
            adjective_form=v["adjective_form"],
        )

        response = auth_client.delete(
            detail_url(WORD_FORMS_URL, v["adjective_form"].id)
        )

        assert response.status_code == 204
        pair.refresh_from_db()
        assert pair.adjective_form is None
        assert auth_client.get(detail_url(PAIRS_URL, pair.id)).json() == pair_body(pair)

    def test_required_fields(self, auth_client, db):
        response = auth_client.post(WORD_FORMS_URL, {}, format="json")

        assert response.status_code == 400
        assert response.json() == {
            "word_id": REQUIRED,
            "case": REQUIRED,
            "number": REQUIRED,
            "word_form": REQUIRED,
        }

    def test_unknown_word_is_rejected(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.post(
            WORD_FORMS_URL,
            {
                "word_id": UNKNOWN_ID,
                "case": v["case_dat"].id,
                "number": v["number_sg"].id,
                "word_form": "дому",
            },
            format="json",
        )

        assert response.status_code == 400
        assert response.json() == {"word_id": invalid_pk()}


# ---------------------------------------------------------------------------
# Contexts
# ---------------------------------------------------------------------------


class TestContexts:
    def test_teacher_creates_a_context(self, auth_client, db):
        response = auth_client.post(
            CONTEXTS_URL, {"text": "В ____ живёт семья"}, format="json"
        )

        assert response.status_code == 201
        context = Context.objects.get()
        assert response.json() == {"id": context.id, "text": "В ____ живёт семья"}

    def test_anonymous_user_reads_a_context(self, api_client, vocabulary):
        context = vocabulary["context"]

        response = api_client.get(detail_url(CONTEXTS_URL, context.id))

        assert response.status_code == 200
        assert response.json() == {"id": context.id, "text": "у ____"}

    def test_teacher_replaces_a_context(self, auth_client, vocabulary):
        context = vocabulary["context"]

        response = auth_client.put(
            detail_url(CONTEXTS_URL, context.id), {"text": "около ____"}, format="json"
        )

        assert response.status_code == 200
        assert response.json() == {"id": context.id, "text": "около ____"}
        context.refresh_from_db()
        assert context.text == "около ____"

    def test_deleting_a_context_deletes_its_pairs(self, auth_client, vocabulary):
        v = vocabulary
        ContextWordFormPair.objects.create(
            context=v["context"], noun_form=v["noun_form"]
        )

        response = auth_client.delete(detail_url(CONTEXTS_URL, v["context"].id))

        assert response.status_code == 204
        assert not Context.objects.exists()
        assert not ContextWordFormPair.objects.exists()
        assert WordForm.objects.filter(id=v["noun_form"].id).exists()

    @pytest.mark.parametrize(
        "text, error",
        [
            ("Без пропуска", "Context must contain '____' as the blank placeholder."),
            ("у ___", "Context must contain '____' as the blank placeholder."),
            (
                "Этот ____ очень ____",
                "Context must contain exactly one '____' placeholder, found more than one.",
            ),
        ],
    )
    def test_text_needs_exactly_one_placeholder(self, auth_client, db, text, error):
        response = auth_client.post(CONTEXTS_URL, {"text": text}, format="json")

        assert response.status_code == 400
        assert response.json() == {"text": [error]}
        assert not Context.objects.exists()

    @pytest.mark.parametrize("text", ["без пропуска", "____ и ещё ____"])
    def test_update_keeps_the_placeholder_rule(self, auth_client, vocabulary, text):
        context = vocabulary["context"]

        response = auth_client.put(
            detail_url(CONTEXTS_URL, context.id), {"text": text}, format="json"
        )

        assert response.status_code == 400
        assert list(response.json()) == ["text"]
        context.refresh_from_db()
        assert context.text == "у ____"

    def test_duplicate_text_is_rejected(self, auth_client, vocabulary):
        response = auth_client.post(CONTEXTS_URL, {"text": "у ____"}, format="json")

        assert response.status_code == 400
        assert response.json() == {"text": ["Контекст with this text already exists."]}
        assert Context.objects.count() == 1

    def test_text_is_required(self, auth_client, db):
        response = auth_client.post(CONTEXTS_URL, {}, format="json")

        assert response.status_code == 400
        assert response.json() == {"text": REQUIRED}


# ---------------------------------------------------------------------------
# Context-word-form pairs
# ---------------------------------------------------------------------------


class TestPairs:
    def test_teacher_creates_a_noun_only_pair(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.post(
            PAIRS_URL,
            {
                "context_id": v["context"].id,
                "noun_form_id": v["noun_form"].id,
                "adjective_form_id": None,
            },
            format="json",
        )

        assert response.status_code == 201
        pair = ContextWordFormPair.objects.get()
        assert response.json() == {
            "id": pair.id,
            "context": {"id": v["context"].id, "text": "у ____"},
            "noun_form": word_form_body(v["noun_form"]),
            "adjective_form": None,
        }
        assert (pair.context, pair.noun_form, pair.adjective_form) == (
            v["context"],
            v["noun_form"],
            None,
        )

    def test_teacher_creates_a_pair_with_an_adjective(self, auth_client, vocabulary):
        v = vocabulary

        response = auth_client.post(
            PAIRS_URL,
            {
                "context_id": v["context"].id,
                "noun_form_id": v["noun_form"].id,
                "adjective_form_id": v["adjective_form"].id,
            },
            format="json",
        )

        assert response.status_code == 201
        pair = ContextWordFormPair.objects.get()
        assert response.json() == pair_body(pair)
        assert response.json()["adjective_form"] == word_form_body(v["adjective_form"])

    def test_anonymous_user_reads_a_pair(self, api_client, vocabulary):
        v = vocabulary
        pair = ContextWordFormPair.objects.create(
            context=v["context"],
            noun_form=v["noun_form"],
            adjective_form=v["adjective_form"],
        )

        response = api_client.get(detail_url(PAIRS_URL, pair.id))

        assert response.status_code == 200
        assert response.json() == pair_body(pair)

    def test_teacher_replaces_a_pair(self, auth_client, vocabulary):
        v = vocabulary
        pair = ContextWordFormPair.objects.create(
            context=v["context"], noun_form=v["noun_form"]
        )
        other_context = Context.objects.create(text="около ____")

        response = auth_client.put(
            detail_url(PAIRS_URL, pair.id),
            {
                "context_id": other_context.id,
                "noun_form_id": v["noun_form"].id,
                "adjective_form_id": v["adjective_form"].id,
            },
            format="json",
        )

        assert response.status_code == 200
        pair.refresh_from_db()
        assert response.json() == pair_body(pair)
        assert (pair.context, pair.adjective_form) == (
            other_context,
            v["adjective_form"],
        )

    def test_teacher_removes_the_adjective(self, auth_client, vocabulary):
        v = vocabulary
        pair = ContextWordFormPair.objects.create(
            context=v["context"],
            noun_form=v["noun_form"],
            adjective_form=v["adjective_form"],
        )

        response = auth_client.patch(
            detail_url(PAIRS_URL, pair.id), {"adjective_form_id": None}, format="json"
        )

        assert response.status_code == 200
        assert response.json()["adjective_form"] is None
        pair.refresh_from_db()
        assert pair.adjective_form is None

    def test_teacher_deletes_a_pair(self, auth_client, vocabulary):
        v = vocabulary
        pair = ContextWordFormPair.objects.create(
            context=v["context"], noun_form=v["noun_form"]
        )

        response = auth_client.delete(detail_url(PAIRS_URL, pair.id))

        assert response.status_code == 204
        assert not ContextWordFormPair.objects.exists()
        assert Context.objects.filter(id=v["context"].id).exists()
        assert WordForm.objects.filter(id=v["noun_form"].id).exists()

    def test_create_needs_every_id_field(self, auth_client, db):
        response = auth_client.post(PAIRS_URL, {}, format="json")

        assert response.status_code == 400
        assert response.json() == {"context_id": REQUIRED, "noun_form_id": REQUIRED}

    @pytest.mark.parametrize(
        "field", ["context_id", "noun_form_id", "adjective_form_id"]
    )
    def test_unknown_id_is_rejected(self, auth_client, vocabulary, field):
        v = vocabulary
        body = {
            "context_id": v["context"].id,
            "noun_form_id": v["noun_form"].id,
            "adjective_form_id": v["adjective_form"].id,
            field: UNKNOWN_ID,
        }

        response = auth_client.post(PAIRS_URL, body, format="json")

        assert response.status_code == 400
        assert response.json() == {field: invalid_pk()}
        assert not ContextWordFormPair.objects.exists()
