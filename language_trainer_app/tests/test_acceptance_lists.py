"""Acceptance tests for the contexts list and the context-word-form pairs list.

Each test follows a real flow through the HTTP API. The teacher logs in with
a password and sends the JWT, as the frontend does.
"""

import pytest
from rest_framework.test import APIClient

from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.tests.conftest import make_csv_file

CONTEXTS_URL = "/contexts/"
PAIRS_URL = "/context-word-form-pairs/"
IMPORT_CONTEXTS_URL = "/api/import/contexts/"

# The default page size is 100. The bug hid every row after it.
DEFAULT_PAGE_SIZE = 100
ROWS_ABOVE_PAGE_SIZE = 120


def context_texts(count):
    return [f"Контекст {number:03d} ____" for number in range(count)]


def import_contexts(client, texts):
    csv_content = "text\n" + "\n".join(texts) + "\n"
    response = client.post(
        IMPORT_CONTEXTS_URL, {"file": make_csv_file(csv_content)}, format="multipart"
    )
    assert response.status_code == 200
    assert response.data["created"] == len(texts)


def make_noun_form(reference_data, base_form="дом"):
    word = Word.objects.create(
        base_form=base_form,
        part_of_speech=reference_data["pos_noun"],
        gender=reference_data["gender_m"],
    )
    return WordForm.objects.create(
        word=word,
        case=reference_data["case_nom"],
        gender=None,
        number=reference_data["number_sg"],
        word_form=base_form,
    )


def make_pairs(reference_data, count):
    noun_form = make_noun_form(reference_data)
    contexts = Context.objects.bulk_create(
        Context(text=text) for text in context_texts(count)
    )
    return ContextWordFormPair.objects.bulk_create(
        ContextWordFormPair(context=context, noun_form=noun_form)
        for context in contexts
    )


@pytest.fixture
def teacher_client(teacher_user):
    client = APIClient()
    response = client.post(
        "/auth/login/",
        {"username": "teacher", "password": "pass1234"},
        format="json",
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


class TestContextsList:
    def test_teacher_sees_every_imported_context(self, teacher_client):
        texts = context_texts(ROWS_ABOVE_PAGE_SIZE)
        import_contexts(teacher_client, texts)

        response = teacher_client.get(CONTEXTS_URL)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert [context["text"] for context in response.data] == sorted(texts)

    def test_list_follows_create_and_delete_above_page_size(self, teacher_client):
        import_contexts(teacher_client, context_texts(ROWS_ABOVE_PAGE_SIZE))
        # This text sorts after all imported contexts.
        new_text = "Яблоко лежит на ____"

        created = teacher_client.post(CONTEXTS_URL, {"text": new_text}, format="json")
        assert created.status_code == 201

        after_create = teacher_client.get(CONTEXTS_URL)
        assert len(after_create.data) == ROWS_ABOVE_PAGE_SIZE + 1
        assert after_create.data[-1] == {"id": created.data["id"], "text": new_text}

        deleted = teacher_client.delete(f"{CONTEXTS_URL}{created.data['id']}/")
        assert deleted.status_code == 204

        after_delete = teacher_client.get(CONTEXTS_URL)
        assert len(after_delete.data) == ROWS_ABOVE_PAGE_SIZE
        assert new_text not in [context["text"] for context in after_delete.data]

    def test_anonymous_user_sees_every_context(self, api_client, db):
        texts = context_texts(ROWS_ABOVE_PAGE_SIZE)
        Context.objects.bulk_create(Context(text=text) for text in texts)

        response = api_client.get(CONTEXTS_URL)

        assert response.status_code == 200
        assert [context["text"] for context in response.data] == sorted(texts)

    def test_empty_list_is_an_empty_array(self, api_client, db):
        response = api_client.get(CONTEXTS_URL)

        assert response.status_code == 200
        assert response.data == []


class TestPairsList:
    def test_teacher_creates_pair_for_context_above_page_size(
        self, teacher_client, reference_data
    ):
        import_contexts(teacher_client, context_texts(ROWS_ABOVE_PAGE_SIZE))
        noun_form = make_noun_form(reference_data)
        last_context = teacher_client.get(CONTEXTS_URL).data[-1]

        created = teacher_client.post(
            PAIRS_URL,
            {
                "context_id": last_context["id"],
                "noun_form_id": noun_form.id,
                "adjective_form_id": None,
            },
            format="json",
        )
        assert created.status_code == 201

        response = teacher_client.get(PAIRS_URL)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["id"] == created.data["id"]
        assert response.data[0]["context"] == last_context
        assert response.data[0]["noun_form"]["id"] == noun_form.id

    def test_teacher_sees_every_pair(self, teacher_client, reference_data):
        pairs = make_pairs(reference_data, DEFAULT_PAGE_SIZE + 1)

        response = teacher_client.get(PAIRS_URL)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert {pair["id"] for pair in response.data} == {pair.id for pair in pairs}

    def test_anonymous_user_sees_every_pair(self, api_client, reference_data):
        make_pairs(reference_data, DEFAULT_PAGE_SIZE + 1)

        response = api_client.get(PAIRS_URL)

        assert response.status_code == 200
        assert len(response.data) == DEFAULT_PAGE_SIZE + 1

    def test_empty_list_is_an_empty_array(self, api_client, db):
        response = api_client.get(PAIRS_URL)

        assert response.status_code == 200
        assert response.data == []


class TestLargeListsStayPaginated:
    """Words and word forms have too many rows to send in one response."""

    @pytest.fixture
    def words_above_page_size(self, reference_data):
        words = Word.objects.bulk_create(
            Word(
                base_form=f"слово{number:03d}",
                part_of_speech=reference_data["pos_noun"],
                gender=reference_data["gender_m"],
            )
            for number in range(DEFAULT_PAGE_SIZE + 1)
        )
        WordForm.objects.bulk_create(
            WordForm(
                word=word,
                case=reference_data["case_nom"],
                gender=None,
                number=reference_data["number_sg"],
                word_form=word.base_form,
            )
            for word in words
        )

    @pytest.mark.parametrize("url", ["/words/", "/word-forms/"])
    def test_list_returns_one_page(self, api_client, words_above_page_size, url):
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == DEFAULT_PAGE_SIZE + 1
        assert len(response.data["results"]) == DEFAULT_PAGE_SIZE
        assert response.data["next"] is not None
