"""Acceptance tests for the flow: a developer opens the Django admin.

A superuser logs in through the admin login form. Each registered model has a
list page with a search, and a change page. The lookup tables use the rows that
the migrations add. Search terms keep the case of the stored text, because
SQLite ignores case only for ASCII letters and PostgreSQL ignores it for all.
"""

import re
from html import unescape

import pytest
from django.contrib.auth.models import User

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.phrase import Phrase
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber

ADMIN_URL = "/admin/"
LOGIN_URL = "/admin/login/"
APP_URL = "/admin/language_trainer_app/"
LIVE_SEARCH_JS = '<script src="/static/language_trainer_app/admin/live_search.js">'
EMPTY = "-"

USERNAME = "developer"
PASSWORD = "admin-pass-1234"

ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r'<t[dh] class="field-(\w+)[^"]*"[^>]*>(.*?)</t[dh]>', re.S)
FILTER = re.compile(r'<details data-filter-title="([^"]*)"[^>]*>(.*?)</details>', re.S)
LINK = re.compile(r'<a href="([^"]*)">(.*?)</a>', re.S)
TAG = re.compile(r"<[^>]+>")


def text_of(fragment):
    return unescape(TAG.sub("", fragment)).strip()


def result_rows(response):
    """The rows of the change list, as {column: shown text}."""
    html = response.content.decode()
    if 'id="result_list"' not in html:
        return []
    table = html.split('id="result_list"', 1)[1].split("</table>", 1)[0]
    body = table.split("<tbody>", 1)[1]
    return [
        {name: text_of(cell) for name, cell in CELL.findall(row)}
        for row in ROW.findall(body)
    ]


def filters_of(response):
    """The sidebar filters, as {title: {shown choice: link}}."""
    return {
        unescape(title): {
            text_of(label): unescape(href) for href, label in LINK.findall(body)
        }
        for title, body in FILTER.findall(response.content.decode())
    }


def list_url(model):
    return f"{APP_URL}{model._meta.model_name}/"


def change_url(obj):
    return f"{list_url(type(obj))}{obj.pk}/change/"


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username=USERNAME, password=PASSWORD)


@pytest.fixture
def developer_client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def rows(db):
    """For each model a row that a search finds and a row that it does not find."""
    masculine = Gender.objects.get(name="Мужской")
    feminine = Gender.objects.get(name="Женский")
    noun = PartOfSpeech.objects.get(name="Существительное")
    adjective = PartOfSpeech.objects.get(name="Прилагательное")
    nominative = Case.objects.get(name="Именительный")
    genitive = Case.objects.get(name="Родительный")
    singular = WordNumber.objects.get(name="Единственное")
    plural = WordNumber.objects.get(name="Множественное")
    house = Word.objects.create(
        base_form="дом",
        gender=masculine,
        part_of_speech=noun,
        animacy=Word.Animacy.INANIMATE,
    )
    cat = Word.objects.create(
        base_form="кошка",
        gender=feminine,
        part_of_speech=noun,
        animacy=Word.Animacy.ANIMATE,
    )
    big = Word.objects.create(base_form="большой", part_of_speech=adjective)
    house_genitive = WordForm.objects.create(
        word=house, case=genitive, number=singular, word_form="дома"
    )
    cats = WordForm.objects.create(
        word=cat, case=nominative, number=plural, word_form="кошки"
    )
    big_genitive = WordForm.objects.create(
        word=big, case=genitive, gender=masculine, number=singular, word_form="большого"
    )
    near = Context.objects.create(text="у ____")
    see = Context.objects.create(text="я вижу ____")
    pair_with_adjective = ContextWordFormPair.objects.create(
        context=near, noun_form=house_genitive, adjective_form=big_genitive
    )
    noun_only_pair = ContextWordFormPair.objects.create(context=see, noun_form=cats)
    on_table = Phrase.objects.create(phrase_start="на столе")
    on_table.valid_words.set([house])
    under_window = Phrase.objects.create(phrase_start="под окном")
    return {
        "masculine": masculine,
        "feminine": feminine,
        "noun": noun,
        "adjective": adjective,
        "nominative": nominative,
        "genitive": genitive,
        "singular": singular,
        "plural": plural,
        "house": house,
        "cat": cat,
        "big": big,
        "house_genitive": house_genitive,
        "cats": cats,
        "big_genitive": big_genitive,
        "near": near,
        "see": see,
        "pair_with_adjective": pair_with_adjective,
        "noun_only_pair": noun_only_pair,
        "on_table": on_table,
        "under_window": under_window,
    }


def name_row(obj):
    return {"id": str(obj.id), "name": obj.name}


def word_row(word, animacy):
    return {
        "id": str(word.id),
        "base_form": word.base_form,
        "gender": word.gender.name if word.gender else EMPTY,
        "part_of_speech": word.part_of_speech.name,
        "animacy": animacy,
    }


def word_form_row(form):
    return {
        "id": str(form.id),
        "word_form": form.word_form,
        "word": form.word.base_form,
        "case": form.case.name,
        "gender": form.gender.name if form.gender else EMPTY,
        "number": form.number.name,
    }


def pair_row(pair):
    return {
        "id": str(pair.id),
        "context": pair.context.text,
        "noun_form": pair.noun_form.word_form,
        "adjective_form": (
            pair.adjective_form.word_form if pair.adjective_form else EMPTY
        ),
    }


# ---------------------------------------------------------------------------
# Log in
# ---------------------------------------------------------------------------


def test_a_superuser_logs_in_through_the_form_and_sees_every_model(client, superuser):
    response = client.post(
        f"{LOGIN_URL}?next={ADMIN_URL}",
        {"username": USERNAME, "password": PASSWORD, "next": ADMIN_URL},
        follow=True,
    )

    assert response.redirect_chain == [(ADMIN_URL, 302)]
    html = response.content.decode()
    for model, title in [
        (Case, "Падежи"),
        (Context, "Контексты"),
        (ContextWordFormPair, "Пары контекст-форма"),
        (Gender, "Роды"),
        (PartOfSpeech, "Части речи"),
        (Phrase, "Phrases"),
        (Word, "Слова"),
        (WordForm, "Формы слов"),
        (WordNumber, "Числа"),
    ]:
        assert f'<a href="{list_url(model)}">{title}</a>' in html


# ---------------------------------------------------------------------------
# List pages and search
# ---------------------------------------------------------------------------

SEARCHES = {
    "case": (Case, "Роди", "genitive", "nominative"),
    "gender": (Gender, "Муж", "masculine", "feminine"),
    "part of speech": (PartOfSpeech, "Прилаг", "adjective", "noun"),
    "word number": (WordNumber, "Множ", "plural", "singular"),
    "word": (Word, "кош", "cat", "house"),
    "word form by its text": (WordForm, "дома", "house_genitive", "cats"),
    "word form by its base form": (WordForm, "большой", "big_genitive", "cats"),
    "context": (Context, "вижу", "see", "near"),
    "pair by its context": (
        ContextWordFormPair,
        "вижу",
        "noun_only_pair",
        "pair_with_adjective",
    ),
    "pair by its noun form": (
        ContextWordFormPair,
        "дома",
        "pair_with_adjective",
        "noun_only_pair",
    ),
    "phrase": (Phrase, "стол", "on_table", "under_window"),
}


def expected_row(obj):
    if isinstance(obj, (Case, Gender, PartOfSpeech, WordNumber)):
        return name_row(obj)
    if isinstance(obj, Word):
        return word_row(obj, obj.get_animacy_display() or EMPTY)
    if isinstance(obj, WordForm):
        return word_form_row(obj)
    if isinstance(obj, ContextWordFormPair):
        return pair_row(obj)
    if isinstance(obj, Context):
        return {"id": str(obj.id), "text": obj.text}
    return {"id": str(obj.id), "phrase_start": obj.phrase_start}


@pytest.mark.parametrize("search", SEARCHES.values(), ids=SEARCHES.keys())
def test_the_search_on_a_list_page_finds_only_the_matching_row(
    developer_client, rows, search
):
    model, term, hit_key, miss_key = search
    hit, miss = rows[hit_key], rows[miss_key]

    everything = developer_client.get(list_url(model))
    found = developer_client.get(list_url(model), {"q": term})

    assert expected_row(hit) in result_rows(everything)
    assert expected_row(miss) in result_rows(everything)
    assert result_rows(found) == [expected_row(hit)]


# Counting all rows of the big tables is slow, so their pages do not do it.
RESULT_COUNTS = {
    "case": (Case, "Роди", "6 total"),
    "gender": (Gender, "Муж", "3 total"),
    "part of speech": (PartOfSpeech, "Прилаг", "2 total"),
    "word number": (WordNumber, "Множ", "2 total"),
    "context": (Context, "вижу", "2 total"),
    "pair": (ContextWordFormPair, "вижу", "2 total"),
    "phrase": (Phrase, "стол", "2 total"),
    "word": (Word, "кош", "Show all"),
    "word form": (WordForm, "дома", "Show all"),
}


@pytest.mark.parametrize(
    "model, term, all_rows", RESULT_COUNTS.values(), ids=RESULT_COUNTS.keys()
)
def test_a_search_counts_all_rows_only_on_small_tables(
    developer_client, rows, model, term, all_rows
):
    response = developer_client.get(list_url(model), {"q": term})

    assert f'1 result (<a href="?">{all_rows}</a>)' in response.content.decode()


@pytest.mark.parametrize("model", [Word, WordForm])
def test_the_big_tables_search_while_the_developer_types(developer_client, model):
    response = developer_client.get(list_url(model))

    assert LIVE_SEARCH_JS in response.content.decode()


# ---------------------------------------------------------------------------
# List filters
# ---------------------------------------------------------------------------


def test_the_word_list_filters_by_gender_part_of_speech_and_animacy(
    developer_client, rows
):
    filters = filters_of(developer_client.get(list_url(Word)))

    assert set(filters) == {"gender", "part of speech", "animacy"}
    assert {"Мужской", "Женский"} <= set(filters["gender"])
    assert {"Существительное", "Прилагательное"} <= set(filters["part of speech"])
    assert {"Одушевлённое", "Неодушевлённое"} <= set(filters["animacy"])

    animate = developer_client.get(list_url(Word) + filters["animacy"]["Одушевлённое"])
    assert result_rows(animate) == [word_row(rows["cat"], "Одушевлённое")]


def test_the_word_form_list_filters_by_case_gender_and_number(developer_client, rows):
    filters = filters_of(developer_client.get(list_url(WordForm)))

    assert set(filters) == {"case", "gender", "number"}
    assert {"Именительный", "Родительный"} <= set(filters["case"])
    assert {"Мужской", "Женский"} <= set(filters["gender"])
    assert {"Единственное", "Множественное"} <= set(filters["number"])

    plural = developer_client.get(
        list_url(WordForm) + filters["number"]["Множественное"]
    )
    assert result_rows(plural) == [word_form_row(rows["cats"])]


def test_the_pair_list_filters_by_the_noun_form(developer_client, rows):
    filters = filters_of(developer_client.get(list_url(ContextWordFormPair)))

    assert set(filters) == {"case", "gender", "number"}
    assert {"Именительный", "Родительный"} <= set(filters["case"])
    assert {"Единственное", "Множественное"} <= set(filters["number"])

    genitive = developer_client.get(
        list_url(ContextWordFormPair) + filters["case"]["Родительный"]
    )
    assert result_rows(genitive) == [pair_row(rows["pair_with_adjective"])]


# ---------------------------------------------------------------------------
# Change pages
# ---------------------------------------------------------------------------

TITLES = {
    "case": ("genitive", "Родительный"),
    "gender": ("masculine", "Мужской"),
    "part of speech": ("noun", "Существительное"),
    "word number": ("plural", "Множественное"),
    "word": ("cat", "кошка"),
    "word form": ("big_genitive", "большого"),
    "context": ("see", "я вижу ____"),
    "pair with an adjective": ("pair_with_adjective", "у ____: большого дома"),
    "pair without an adjective": ("noun_only_pair", "я вижу ____: кошки"),
    "phrase": ("on_table", "на столе"),
}


@pytest.mark.parametrize("key, title", TITLES.values(), ids=TITLES.keys())
def test_the_change_page_names_the_row(developer_client, rows, key, title):
    response = developer_client.get(change_url(rows[key]))

    headings = re.findall(r"<h2>(.*?)</h2>", response.content.decode(), re.S)
    # The browser shows each run of spaces as one space.
    assert title in [" ".join(text_of(h).split()) for h in headings]


def raw_id_field(name, obj, label):
    """The text input for the id, then the name of the row it points to."""
    return re.compile(
        rf'<input type="text" name="{name}" value="{obj.pk}"[^>]*'
        rf'class="vForeignKeyRawIdAdminField">.*?'
        rf'<strong><a href="{change_url(obj)}">{re.escape(label)}</a></strong>',
        re.S,
    )


def test_the_word_form_page_asks_for_the_word_id(developer_client, rows):
    form = rows["house_genitive"]

    html = developer_client.get(change_url(form)).content.decode()

    assert raw_id_field("word", form.word, "дом").search(html)


def test_the_pair_page_asks_for_the_ids_of_the_context_and_the_forms(
    developer_client, rows
):
    pair = rows["pair_with_adjective"]

    html = developer_client.get(change_url(pair)).content.decode()

    assert raw_id_field("context", pair.context, "у ____").search(html)
    assert raw_id_field("noun_form", pair.noun_form, "дома").search(html)
    assert raw_id_field("adjective_form", pair.adjective_form, "большого").search(html)


def test_the_phrase_page_picks_valid_words_in_two_boxes(developer_client, rows):
    html = developer_client.get(change_url(rows["on_table"])).content.decode()

    select = re.search(r'<select name="valid_words"[^>]*>(.*?)</select>', html, re.S)
    assert 'class="selectfilter"' in select.group(0)
    options = re.findall(
        r'<option value="(\d+)"( selected)?>(.*?)</option>', select.group(1)
    )
    assert (str(rows["house"].id), " selected", "дом") in options
    assert (str(rows["cat"].id), "", "кошка") in options
