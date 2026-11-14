"""Acceptance tests for the flow: a teacher searches words and word forms.

The same tests run on SQLite and on PostgreSQL. SQLite LIKE ignores case only
for ASCII, so partial search with Cyrillic in a different case is tested on
PostgreSQL only, the database of production.
"""

import pytest
from django.db import connection

from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber

WORDS_URL = "/words/"
WORD_FORMS_URL = "/word-forms/"


def make_word(rd, base_form, pos="pos_noun", gender="gender_m", animacy=None):
    return Word.objects.create(
        base_form=base_form,
        part_of_speech=rd[pos],
        gender=rd[gender] if gender else None,
        animacy=animacy,
    )


def make_form(rd, word, word_form, case="case_nom", number=None, gender=None):
    return WordForm.objects.create(
        word=word,
        case=rd[case],
        gender=rd[gender] if gender else None,
        number=number or rd["number_sg"],
        word_form=word_form,
    )


def search(api_client, url, **params):
    response = api_client.get(url, params)
    assert response.status_code == 200
    assert response.data["count"] == len(response.data["results"])
    return [row["id"] for row in response.data["results"]]


def ids(*rows):
    return [row.id for row in rows]


@pytest.fixture
def words(reference_data):
    rd = reference_data
    nouns = ("бездомник", "домовой", "дом", "домик", "кошка")
    words = {base_form: make_word(rd, base_form) for base_form in nouns}
    words["домашний"] = make_word(rd, "домашний", pos="pos_adj", gender=None)
    return words


@pytest.fixture
def same_base_form_words(reference_data):
    """'рабочий' is both a noun (a worker) and an adjective (working)."""
    rd = reference_data
    noun = make_word(rd, "рабочий", animacy=Word.Animacy.ANIMATE)
    adjective = make_word(rd, "рабочий", pos="pos_adj", gender=None)
    noun_form = make_form(rd, noun, "рабочего", case="case_gen")
    adjective_form = make_form(
        rd, adjective, "рабочего", case="case_gen", gender="gender_m"
    )
    return {
        "noun": noun,
        "adjective": adjective,
        "noun_form": noun_form,
        "adjective_form": adjective_form,
        "noun_nominative": make_form(rd, noun, "рабочий"),
    }


@pytest.fixture
def name_and_noun(reference_data):
    """The name 'Надежда' is added before the noun 'надежда', so it has the lower id."""
    rd = reference_data
    name = make_word(rd, "Надежда", gender="gender_f")
    noun = make_word(rd, "надежда", gender="gender_f")
    return {
        "name": name,
        "noun": noun,
        "name_form": make_form(rd, name, "Надежде", case="case_dat"),
        "noun_form": make_form(rd, noun, "надежде", case="case_dat"),
    }


class TestWordPartialSearch:
    def test_lists_prefix_matches_before_contains_matches(self, api_client, words):
        found = search(api_client, WORDS_URL, search="дом")

        assert found == ids(
            words["дом"],
            words["домашний"],
            words["домик"],
            words["домовой"],
            words["бездомник"],
        )

    @pytest.mark.parametrize(
        "term, expected",
        [
            ("доми", ["домик"]),
            ("ом", ["бездомник", "дом", "домашний", "домик", "домовой"]),
        ],
    )
    def test_without_exact_match_ranks_prefix_then_contains_by_base_form(
        self, api_client, words, term, expected
    ):
        found = search(api_client, WORDS_URL, search=term)

        assert found == ids(*(words[base_form] for base_form in expected))

    @pytest.mark.parametrize("params", [{}, {"search": ""}, {"search": "  "}])
    def test_empty_search_lists_all_words_by_base_form(self, api_client, words, params):
        found = search(api_client, WORDS_URL, **params)

        assert found == ids(*(words[base_form] for base_form in sorted(words)))

    def test_no_match_returns_no_words(self, api_client, words):
        assert search(api_client, WORDS_URL, search="ящик") == []

    def test_part_of_speech_filter_without_search(
        self, api_client, words, reference_data
    ):
        found = search(
            api_client, WORDS_URL, part_of_speech=reference_data["pos_adj"].id
        )

        assert found == ids(words["домашний"])

    def test_part_of_speech_filter_narrows_partial_search(
        self, api_client, words, reference_data
    ):
        found = search(
            api_client,
            WORDS_URL,
            search="дом",
            part_of_speech=reference_data["pos_noun"].id,
        )

        assert found == ids(
            words["дом"], words["домик"], words["домовой"], words["бездомник"]
        )


class TestWordExactSearch:
    def test_returns_only_whole_word_matches(self, api_client, words):
        found = search(api_client, WORDS_URL, search="дом", match="exact")

        assert found == ids(words["дом"])

    def test_match_mode_ignores_case_and_spaces(self, api_client, words):
        found = search(api_client, WORDS_URL, search=" дом ", match=" EXACT ")

        assert found == ids(words["дом"])

    def test_no_match_returns_no_words(self, api_client, words):
        assert search(api_client, WORDS_URL, search="до", match="exact") == []

    def test_returns_every_part_of_speech_with_that_base_form_newest_first(
        self, api_client, same_base_form_words
    ):
        found = search(api_client, WORDS_URL, search="рабочий", match="exact")

        assert found == ids(
            same_base_form_words["adjective"], same_base_form_words["noun"]
        )

    def test_row_has_the_fields_the_frontend_reads(
        self, api_client, reference_data, same_base_form_words
    ):
        response = api_client.get(
            WORDS_URL,
            {
                "search": "рабочий",
                "match": "exact",
                "part_of_speech": reference_data["pos_noun"].id,
            },
        )

        assert response.status_code == 200
        assert response.json()["results"] == [
            {
                "id": same_base_form_words["noun"].id,
                "base_form": "рабочий",
                "part_of_speech": reference_data["pos_noun"].id,
                "gender": reference_data["gender_m"].id,
                "animacy": "Anim",
            }
        ]

    @pytest.mark.parametrize("pos", ["noun", "adjective"])
    def test_part_of_speech_filter_narrows_exact_search(
        self, api_client, reference_data, same_base_form_words, pos
    ):
        pos_id = reference_data["pos_noun" if pos == "noun" else "pos_adj"].id

        found = search(
            api_client,
            WORDS_URL,
            search="рабочий",
            match="exact",
            part_of_speech=pos_id,
        )

        assert found == ids(same_base_form_words[pos])

    @pytest.mark.parametrize(
        "term, expected",
        [("надежда", ["noun", "name"]), ("Надежда", ["name", "noun"])],
    )
    def test_exact_case_match_comes_first(
        self, api_client, name_and_noun, term, expected
    ):
        found = search(api_client, WORDS_URL, search=term, match="exact")

        assert found == ids(*(name_and_noun[key] for key in expected))

    def test_upper_case_search_finds_cyrillic_words_in_any_case(
        self, api_client, name_and_noun
    ):
        found = search(api_client, WORDS_URL, search="НАДЕЖДА", match="exact")

        assert sorted(found) == sorted(
            ids(name_and_noun["name"], name_and_noun["noun"])
        )

    def test_lower_case_search_finds_capitalised_word(self, api_client, reference_data):
        moscow = make_word(reference_data, "Москва", gender="gender_f")

        found = search(api_client, WORDS_URL, search="москва", match="exact")

        assert found == ids(moscow)


@pytest.fixture
def person_forms(reference_data):
    """'человек' has the plural 'люди', which does not contain the base form."""
    rd = reference_data
    plural = WordNumber.objects.create(name="множественное")
    person = make_word(rd, "человек")
    god_man = make_word(rd, "богочеловек")
    # Forms with the same rank are added out of alphabetical order.
    return {
        "человеку": make_form(rd, person, "человеку", case="case_dat"),
        "человека": make_form(rd, person, "человека", case="case_gen"),
        "человек": make_form(rd, person, "человек"),
        "люди": make_form(rd, person, "люди", number=plural),
        "богочеловека": make_form(rd, god_man, "богочеловека", case="case_gen"),
        "кошке": make_form(
            rd, make_word(rd, "кошка", gender="gender_f"), "кошке", case="case_dat"
        ),
    }


@pytest.fixture
def pronoun_forms(reference_data):
    """'ей' (of 'она') sorts before 'ему' (of 'он'), against their ranks for 'он'."""
    rd = dict(reference_data, pos_pron=PartOfSpeech.objects.create(name="местоимение"))
    he = make_word(rd, "он", pos="pos_pron")
    she = make_word(rd, "она", pos="pos_pron", gender="gender_f")
    return {
        "она": make_form(rd, she, "она"),
        "ей": make_form(rd, she, "ей", case="case_dat"),
        "ему": make_form(rd, he, "ему", case="case_dat"),
        "он": make_form(rd, he, "он"),
    }


class TestWordFormPartialSearch:
    def test_base_form_equal_to_term_ranks_before_base_form_prefix(
        self, api_client, pronoun_forms
    ):
        found = search(api_client, WORD_FORMS_URL, search="он")

        assert found == ids(
            *(pronoun_forms[form] for form in ("он", "она", "ему", "ей"))
        )

    @pytest.mark.parametrize(
        "term, expected",
        [
            # word form exact, word form prefix, base form exact, contains
            ("человек", ["человек", "человека", "человеку", "люди", "богочеловека"]),
            # word form prefix, base form prefix, contains
            ("чел", ["человек", "человека", "человеку", "люди", "богочеловека"]),
            ("люд", ["люди"]),
        ],
    )
    def test_ranks_word_form_matches_before_base_form_matches(
        self, api_client, person_forms, term, expected
    ):
        found = search(api_client, WORD_FORMS_URL, search=term)

        assert found == ids(*(person_forms[form] for form in expected))

    @pytest.mark.parametrize("params", [{}, {"search": ""}])
    def test_empty_search_lists_all_word_forms(self, api_client, person_forms, params):
        found = search(api_client, WORD_FORMS_URL, **params)

        assert sorted(found) == sorted(ids(*person_forms.values()))

    def test_no_match_returns_no_word_forms(self, api_client, person_forms):
        assert search(api_client, WORD_FORMS_URL, search="ящик") == []

    def test_part_of_speech_filter_without_search(
        self, api_client, reference_data, same_base_form_words
    ):
        found = search(
            api_client,
            WORD_FORMS_URL,
            word_part_of_speech=reference_data["pos_adj"].id,
        )

        assert found == ids(same_base_form_words["adjective_form"])

    def test_part_of_speech_filter_narrows_partial_search(
        self, api_client, reference_data, same_base_form_words
    ):
        found = search(
            api_client,
            WORD_FORMS_URL,
            search="рабоч",
            word_part_of_speech=reference_data["pos_noun"].id,
        )

        assert found == ids(
            same_base_form_words["noun_form"], same_base_form_words["noun_nominative"]
        )


class TestWordFormExactSearch:
    @pytest.mark.parametrize("search_field", [None, "word_form", "something_else"])
    def test_matches_whole_word_form_by_default(
        self, api_client, person_forms, search_field
    ):
        params = {"search": "человек", "match": "exact"}
        if search_field:
            params["search_field"] = search_field

        found = search(api_client, WORD_FORMS_URL, **params)

        assert found == ids(person_forms["человек"])

    @pytest.mark.parametrize("search_field", ["base_form", " BASE_FORM "])
    def test_base_form_field_returns_every_form_of_that_word(
        self, api_client, person_forms, search_field
    ):
        found = search(
            api_client,
            WORD_FORMS_URL,
            search="человек",
            match="exact",
            search_field=search_field,
        )

        assert sorted(found) == sorted(
            ids(
                person_forms["человек"],
                person_forms["человека"],
                person_forms["человеку"],
                person_forms["люди"],
            )
        )

    @pytest.mark.parametrize("search_field", [None, "base_form"])
    def test_no_match_returns_no_word_forms(
        self, api_client, person_forms, search_field
    ):
        params = {"search": "чел", "match": "exact"}
        if search_field:
            params["search_field"] = search_field

        assert search(api_client, WORD_FORMS_URL, **params) == []

    def test_match_mode_ignores_case_and_spaces(self, api_client, person_forms):
        found = search(api_client, WORD_FORMS_URL, search=" человек ", match=" EXACT ")

        assert found == ids(person_forms["человек"])

    def test_same_word_form_of_two_words_comes_newest_first(
        self, api_client, same_base_form_words
    ):
        found = search(api_client, WORD_FORMS_URL, search="рабочего", match="exact")

        assert found == ids(
            same_base_form_words["adjective_form"], same_base_form_words["noun_form"]
        )

    def test_row_has_the_fields_the_frontend_reads(
        self, api_client, reference_data, same_base_form_words
    ):
        response = api_client.get(
            WORD_FORMS_URL,
            {
                "search": "рабочего",
                "match": "exact",
                "word_part_of_speech": reference_data["pos_adj"].id,
            },
        )

        assert response.status_code == 200
        assert response.json()["results"] == [
            {
                "id": same_base_form_words["adjective_form"].id,
                "word": {
                    "id": same_base_form_words["adjective"].id,
                    "base_form": "рабочий",
                    "part_of_speech": reference_data["pos_adj"].id,
                    "gender": None,
                    "animacy": None,
                },
                "case": reference_data["case_gen"].id,
                "gender": reference_data["gender_m"].id,
                "number": reference_data["number_sg"].id,
                "word_form": "рабочего",
            }
        ]

    def test_part_of_speech_filter_narrows_exact_base_form_search(
        self, api_client, reference_data, same_base_form_words
    ):
        found = search(
            api_client,
            WORD_FORMS_URL,
            search="рабочий",
            match="exact",
            search_field="base_form",
            word_part_of_speech=reference_data["pos_noun"].id,
        )

        assert sorted(found) == sorted(
            ids(
                same_base_form_words["noun_form"],
                same_base_form_words["noun_nominative"],
            )
        )

    @pytest.mark.parametrize("search_field", [None, "base_form"])
    @pytest.mark.parametrize(
        "term, expected",
        [
            ({None: "надежде", "base_form": "надежда"}, ["noun_form", "name_form"]),
            ({None: "Надежде", "base_form": "Надежда"}, ["name_form", "noun_form"]),
        ],
    )
    def test_exact_case_match_comes_first(
        self, api_client, name_and_noun, search_field, term, expected
    ):
        params = {"search": term[search_field], "match": "exact"}
        if search_field:
            params["search_field"] = search_field

        found = search(api_client, WORD_FORMS_URL, **params)

        assert found == ids(*(name_and_noun[key] for key in expected))

    @pytest.mark.parametrize(
        "search_field, term", [(None, "НАДЕЖДЕ"), ("base_form", "НАДЕЖДА")]
    )
    def test_upper_case_search_finds_cyrillic_forms_in_any_case(
        self, api_client, name_and_noun, search_field, term
    ):
        params = {"search": term, "match": "exact"}
        if search_field:
            params["search_field"] = search_field

        found = search(api_client, WORD_FORMS_URL, **params)

        assert sorted(found) == sorted(
            ids(name_and_noun["name_form"], name_and_noun["noun_form"])
        )


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="SQLite LIKE ignores case only for ASCII letters.",
)
def test_partial_search_ignores_cyrillic_case_on_postgresql(api_client, reference_data):
    house = make_word(reference_data, "дом")
    form = make_form(reference_data, house, "дом")

    words = api_client.get(WORDS_URL, {"search": "ДОМ"})
    forms = api_client.get(WORD_FORMS_URL, {"search": "ДОМ"})

    assert [row["id"] for row in words.data["results"]] == [house.id]
    assert [row["id"] for row in forms.data["results"]] == [form.id]
