"""Acceptance tests for the flow: a student generates a test."""

import pytest

from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber

URL = "/tests/generate/"
UNKNOWN_ID = 999999


@pytest.fixture
def rd(reference_data):
    reference_data["number_sg"].name_en = "Singular"
    reference_data["number_sg"].save()
    return reference_data


def make_noun(rd, base_form, gender, animacy=None):
    return Word.objects.create(
        base_form=base_form,
        part_of_speech=rd["pos_noun"],
        gender=gender,
        animacy=animacy,
    )


def make_form(word, case, word_form, number, gender=None):
    return WordForm.objects.create(
        word=word, case=case, gender=gender, number=number, word_form=word_form
    )


def make_pair(context_text, noun_form, adjective_form=None):
    return ContextWordFormPair.objects.create(
        context=Context.objects.create(text=context_text),
        noun_form=noun_form,
        adjective_form=adjective_form,
    )


def generate(api_client, rd, case, use_adjective=False, gender=None, **extra):
    payload = {
        "use_adjective": use_adjective,
        "genders": [(gender or rd["gender_m"]).id],
        "cases": [rd[case].id],
        "numbers": [rd["number_sg"].id],
        **extra,
    }
    return api_client.post(URL, payload, format="json")


@pytest.fixture
def feminine_noun_with_adjective(rd):
    """'красивой машины' in the genitive; the adjective base form is masculine."""
    noun = make_noun(rd, "машина", rd["gender_f"])
    noun_gen = make_form(noun, rd["case_gen"], "машины", rd["number_sg"])
    adjective = Word.objects.create(base_form="красивый", part_of_speech=rd["pos_adj"])
    adjective_gen = make_form(
        adjective, rd["case_gen"], "красивой", rd["number_sg"], rd["gender_f"]
    )
    make_pair("нет ____", noun_gen, adjective_gen)
    return adjective


def test_noun_only_shows_base_form_and_expects_case_form(api_client, rd):
    noun = make_noun(rd, "дом", rd["gender_m"])
    make_pair("у ____", make_form(noun, rd["case_gen"], "дома", rd["number_sg"]))

    response = generate(api_client, rd, "case_gen")

    assert response.status_code == 200
    assert response.json() == [
        {
            "context": "у ____",
            "noun_with_adjective": "дом",
            "correct_answer": "дома",
            "number_name_en": "Singular",
        }
    ]


def test_adjective_hint_is_nominative_form_for_noun_gender(
    api_client, rd, feminine_noun_with_adjective
):
    for word_form, gender in (("красивый", "gender_m"), ("красивая", "gender_f")):
        make_form(
            feminine_noun_with_adjective,
            rd["case_nom"],
            word_form,
            rd["number_sg"],
            rd[gender],
        )

    response = generate(
        api_client, rd, "case_gen", use_adjective=True, gender=rd["gender_f"]
    )

    assert response.status_code == 200
    [item] = response.json()
    assert item["noun_with_adjective"] == "красивая машина"
    assert item["correct_answer"] == "красивой машины"


def test_adjective_hint_is_nominative_form_for_noun_number(api_client, rd):
    number_pl = WordNumber.objects.create(name="множественное", name_en="Plural")
    noun = make_noun(rd, "машина", rd["gender_f"])
    noun_gen_pl = make_form(noun, rd["case_gen"], "машин", number_pl)
    adjective = Word.objects.create(base_form="красивый", part_of_speech=rd["pos_adj"])
    adjective_gen_pl = make_form(
        adjective, rd["case_gen"], "красивых", number_pl, rd["gender_f"]
    )
    for word_form, number in (("красивая", rd["number_sg"]), ("красивые", number_pl)):
        make_form(adjective, rd["case_nom"], word_form, number, rd["gender_f"])
    make_pair("нет ____", noun_gen_pl, adjective_gen_pl)

    response = generate(
        api_client,
        rd,
        "case_gen",
        use_adjective=True,
        gender=rd["gender_f"],
        numbers=[number_pl.id],
    )

    assert response.status_code == 200
    [item] = response.json()
    assert item["noun_with_adjective"] == "красивые машина"
    assert item["correct_answer"] == "красивых машин"
    assert item["number_name_en"] == "Plural"


def test_adjective_hint_falls_back_to_base_form_without_nominative_form(
    api_client, rd, feminine_noun_with_adjective
):
    response = generate(
        api_client, rd, "case_gen", use_adjective=True, gender=rd["gender_f"]
    )

    assert response.status_code == 200
    [item] = response.json()
    assert item["noun_with_adjective"] == "красивый машина"
    assert item["correct_answer"] == "красивой машины"


def test_with_adjective_leaves_out_pairs_without_adjective(
    api_client, rd, feminine_noun_with_adjective
):
    noun = Word.objects.get(base_form="машина")
    make_pair("без ____", WordForm.objects.get(word=noun, case=rd["case_gen"]))

    response = generate(
        api_client, rd, "case_gen", use_adjective=True, gender=rd["gender_f"]
    )

    assert response.status_code == 200
    assert [item["context"] for item in response.json()] == ["нет ____"]


def test_with_adjective_leaves_out_adjectives_in_another_case_or_number(
    api_client, rd, feminine_noun_with_adjective
):
    number_pl = WordNumber.objects.create(name="множественное", name_en="Plural")
    noun = Word.objects.get(base_form="машина")
    noun_gen = WordForm.objects.get(word=noun, case=rd["case_gen"])
    adjective_nom = make_form(
        feminine_noun_with_adjective,
        rd["case_nom"],
        "красивая",
        rd["number_sg"],
        rd["gender_f"],
    )
    adjective_gen_pl = make_form(
        feminine_noun_with_adjective,
        rd["case_gen"],
        "красивых",
        number_pl,
        rd["gender_f"],
    )
    make_pair("другой падеж ____", noun_gen, adjective_nom)
    make_pair("другое число ____", noun_gen, adjective_gen_pl)

    response = generate(
        api_client, rd, "case_gen", use_adjective=True, gender=rd["gender_f"]
    )

    assert response.status_code == 200
    assert [item["context"] for item in response.json()] == ["нет ____"]


def test_noun_filters_keep_only_the_chosen_gender_case_and_number(api_client, rd):
    number_pl = WordNumber.objects.create(name="множественное", name_en="Plural")
    house = make_noun(rd, "дом", rd["gender_m"])
    car = make_noun(rd, "машина", rd["gender_f"])
    make_pair("у ____", make_form(house, rd["case_gen"], "дома", rd["number_sg"]))
    make_pair("у двух ____", make_form(house, rd["case_gen"], "домов", number_pl))
    make_pair("к ____", make_form(house, rd["case_dat"], "дому", rd["number_sg"]))
    make_pair("нет ____", make_form(car, rd["case_gen"], "машины", rd["number_sg"]))

    response = generate(api_client, rd, "case_gen")

    assert response.status_code == 200
    assert [item["correct_answer"] for item in response.json()] == ["дома"]


def test_animacy_filter_keeps_only_matching_nouns(api_client, rd):
    cat = make_noun(rd, "кот", rd["gender_m"], Word.Animacy.ANIMATE)
    table = make_noun(rd, "стол", rd["gender_m"], Word.Animacy.INANIMATE)
    make_pair("вижу ____", make_form(cat, rd["case_gen"], "кота", rd["number_sg"]))
    make_pair("у ____", make_form(table, rd["case_gen"], "стола", rd["number_sg"]))

    response = generate(api_client, rd, "case_gen", animacy="Anim")

    assert response.status_code == 200
    assert [item["correct_answer"] for item in response.json()] == ["кота"]


@pytest.mark.parametrize(
    "field, label",
    [("genders", "gender"), ("cases", "case"), ("numbers", "number")],
)
def test_unknown_id_returns_400_naming_the_id(api_client, rd, field, label):
    response = generate(api_client, rd, "case_gen", **{field: [UNKNOWN_ID]})

    assert response.status_code == 400
    assert response.json() == {field: [f"Invalid {label} IDs: [{UNKNOWN_ID}]"]}


def test_no_matching_pair_returns_empty_list(api_client, rd):
    noun = make_noun(rd, "дом", rd["gender_m"])
    make_pair("это ____", make_form(noun, rd["case_nom"], "дом", rd["number_sg"]))

    response = generate(api_client, rd, "case_gen")

    assert response.status_code == 200
    assert response.json() == []


def test_returns_at_most_ten_items(api_client, rd):
    for i in range(12):
        noun = make_noun(rd, f"дом{i}", rd["gender_m"])
        make_pair(
            f"у ____ {i}",
            make_form(noun, rd["case_gen"], f"дома{i}", rd["number_sg"]),
        )

    response = generate(api_client, rd, "case_gen")

    assert response.status_code == 200
    assert len(response.json()) == 10
