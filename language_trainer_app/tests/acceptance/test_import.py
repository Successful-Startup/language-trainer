"""Integration tests for CSV import API endpoints."""

from dataclasses import dataclass
from typing import Callable

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import QuerySet

from language_trainer_app.models.context import Context
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.tests.conftest import make_csv_file

TEN_MB = 10 * 1024 * 1024


@dataclass(frozen=True)
class ImportEndpoint:
    url: str
    required_headers: list[str]
    header: str
    valid_row: str
    invalid_row: str
    invalid_row_error: str
    blank_row: str
    imported_rows: Callable[[], QuerySet]
    needs_word: bool = False


WORDS = ImportEndpoint(
    url="/api/import/words/",
    required_headers=["base_form", "part_of_speech_name"],
    header="base_form,part_of_speech_name,gender_name,animacy_name",
    valid_row="дом,существительное,мужской,",
    invalid_row="дом,несуществующий,мужской,",
    invalid_row_error="Invalid part_of_speech_name 'несуществующий'",
    blank_row=",,,",
    imported_rows=lambda: Word.objects.filter(base_form="дом"),
)
CONTEXTS = ImportEndpoint(
    url="/api/import/contexts/",
    required_headers=["text"],
    header="text",
    valid_row="я живу в ____",
    invalid_row="без пропуска",
    invalid_row_error="Context must contain '____' as the blank placeholder.",
    blank_row='""',
    imported_rows=lambda: Context.objects.filter(text="я живу в ____"),
)
WORD_FORMS = ImportEndpoint(
    url="/api/import/word-forms/",
    required_headers=[
        "word_base_form",
        "word_part_of_speech_name",
        "word_form",
        "case_name",
        "number_name",
    ],
    header=(
        "word_base_form,word_part_of_speech_name,word_gender_name,"
        "word_form,case_name,form_gender_name,number_name"
    ),
    valid_row="дом,существительное,мужской,дома,родительный,,единственное",
    invalid_row="кот,существительное,мужской,кота,родительный,,единственное",
    invalid_row_error=(
        "Word not found: base_form='кот', part_of_speech='существительное', "
        "gender='мужской'"
    ),
    blank_row=",,,,,,",
    imported_rows=lambda: WordForm.objects.filter(word_form="дома"),
    needs_word=True,
)


@pytest.fixture(
    params=[WORDS, CONTEXTS, WORD_FORMS], ids=["words", "contexts", "word-forms"]
)
def endpoint(request, reference_data):
    spec = request.param
    if spec.needs_word:
        Word.objects.create(
            base_form="дом",
            part_of_speech=reference_data["pos_noun"],
            gender=reference_data["gender_m"],
        )
    return spec


def upload(client, endpoint, content, filename="data.csv"):
    if isinstance(content, str):
        content = content.encode("utf-8")
    file = SimpleUploadedFile(filename, content, content_type="text/csv")
    return client.post(endpoint.url, {"file": file}, format="multipart")


def csv_lines(*lines):
    return "\n".join(lines) + "\n"


class TestEveryImportEndpoint:
    def test_rejects_a_request_without_a_token(self, api_client, endpoint):
        response = upload(
            api_client, endpoint, csv_lines(endpoint.header, endpoint.valid_row)
        )

        assert response.status_code == 401
        assert not endpoint.imported_rows().exists()

    def test_rejects_a_request_without_a_file(self, auth_client, endpoint):
        response = auth_client.post(endpoint.url, {}, format="multipart")

        assert response.status_code == 400
        assert response.data == {"success": False, "error": "No file provided"}

    def test_rejects_a_file_that_is_not_csv(self, auth_client, endpoint):
        content = csv_lines(endpoint.header, endpoint.valid_row)

        response = upload(auth_client, endpoint, content, filename="data.txt")

        assert response.status_code == 400
        assert response.data == {"success": False, "error": "File must be .csv format"}
        assert not endpoint.imported_rows().exists()

    def test_rejects_a_file_above_10_mb(self, auth_client, endpoint):
        content = csv_lines(endpoint.header, endpoint.valid_row).encode("utf-8")
        content += b"\n" * (TEN_MB + 1 - len(content))

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 400
        assert response.data == {"success": False, "error": "File too large (max 10MB)"}
        assert not endpoint.imported_rows().exists()

    def test_rejects_an_empty_file_without_a_header_row(self, auth_client, endpoint):
        response = upload(auth_client, endpoint, "\n")

        assert response.status_code == 400
        assert response.data == {"success": False, "error": "CSV file has no headers"}

    def test_names_the_missing_required_headers(self, auth_client, endpoint):
        response = upload(auth_client, endpoint, csv_lines("comment", "hello"))

        assert response.status_code == 400
        assert response.data == {
            "success": False,
            "error": f"Missing required headers: {endpoint.required_headers}",
        }

    def test_rejects_a_file_that_is_not_utf8(self, auth_client, endpoint):
        content = csv_lines(endpoint.header, endpoint.valid_row).encode("cp1251")

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 400
        assert response.data["success"] is False
        assert response.data["error"].startswith("CSV processing error: ")
        assert not endpoint.imported_rows().exists()

    def test_reads_the_header_of_a_file_with_a_bom(self, auth_client, endpoint):
        content = "\ufeff" + csv_lines(endpoint.header, endpoint.valid_row)

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 200
        assert response.data["created"] == 1
        assert endpoint.imported_rows().count() == 1

    def test_ignores_blank_rows(self, auth_client, endpoint):
        content = csv_lines(
            endpoint.header, endpoint.blank_row, endpoint.valid_row, endpoint.blank_row
        )

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 200
        assert response.data == {
            "success": True,
            "total_rows": 1,
            "created": 1,
            "skipped": 0,
            "errors": 0,
            "error_details": [],
        }

    def test_skips_a_row_that_already_exists(self, auth_client, endpoint):
        content = csv_lines(endpoint.header, endpoint.valid_row, endpoint.valid_row)

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 200
        assert response.data["created"] == 1
        assert response.data["skipped"] == 1
        assert endpoint.imported_rows().count() == 1

    def test_lists_20_errors_and_stops_at_the_21st(self, auth_client, endpoint):
        content = csv_lines(
            endpoint.header, *[endpoint.invalid_row] * 21, endpoint.valid_row
        )

        response = upload(auth_client, endpoint, content)

        assert response.status_code == 200
        assert response.data == {
            "success": False,
            "total_rows": 21,
            "created": 0,
            "skipped": 0,
            "errors": 21,
            "error_details": [
                f"Row {row}: {endpoint.invalid_row_error}" for row in range(2, 22)
            ]
            + ["...and 1 more validation errors"],
        }
        assert not endpoint.imported_rows().exists()


class TestImportWordsEndpoint:
    url = "/api/import/words/"

    def test_successful_import(self, auth_client, reference_data):
        csv_content = (
            "base_form,part_of_speech_name,gender_name\nдом,существительное,мужской\n"
        )
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["created"] == 1
        assert Word.objects.filter(base_form="дом").exists()

    def test_reports_error_for_invalid_pos(self, auth_client, reference_data):
        csv_content = (
            "base_form,part_of_speech_name,gender_name\nдом,несуществующий,мужской\n"
        )
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0

    def test_partial_success_when_some_rows_fail(self, auth_client, reference_data):
        """Valid rows commit; invalid rows are skipped and reported as errors.

        The transaction does NOT roll back on per-row errors — errors are
        collected and the successful rows are kept.
        """
        csv_content = (
            "base_form,part_of_speech_name,gender_name\n"
            "дом,существительное,мужской\n"
            "кот,несуществующий,мужской\n"
        )
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["created"] == 1
        assert response.data["errors"] == 1

    def test_rejects_a_row_without_a_base_form(self, auth_client, reference_data):
        content = csv_lines(WORDS.header, ",существительное,мужской,")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 0
        assert response.data["error_details"] == ["Row 2: base_form is required"]
        assert not Word.objects.exists()

    def test_imports_a_short_row_with_the_optional_columns_blank(
        self, auth_client, reference_data
    ):
        content = csv_lines(WORDS.header, "идти,существительное")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 1
        assert response.data["error_details"] == []
        word = Word.objects.get(base_form="идти")
        assert word.gender is None
        assert word.animacy is None

    def test_names_the_required_column_missing_from_a_short_row(
        self, auth_client, reference_data
    ):
        content = csv_lines(WORDS.header, "идти")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 0
        assert response.data["error_details"] == [
            "Row 2: part_of_speech_name is required"
        ]

    @pytest.mark.parametrize(
        "animacy_name, animacy",
        [
            ("Одушевлённое", Word.Animacy.ANIMATE),
            ("неодушевленное", Word.Animacy.INANIMATE),
        ],
    )
    def test_saves_the_animacy(
        self, auth_client, reference_data, animacy_name, animacy
    ):
        content = csv_lines(WORDS.header, f"кот,существительное,мужской,{animacy_name}")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 1
        assert Word.objects.get(base_form="кот").animacy == animacy

    def test_saves_no_animacy_when_the_column_is_blank(
        self, auth_client, reference_data
    ):
        content = csv_lines(WORDS.header, "кот,существительное,мужской, ")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 1
        assert Word.objects.get(base_form="кот").animacy is None

    def test_rejects_an_unknown_animacy(self, auth_client, reference_data):
        content = csv_lines(WORDS.header, "кот,существительное,мужской,живое")

        response = upload(auth_client, WORDS, content)

        assert response.data["created"] == 0
        assert response.data["error_details"] == [
            "Row 2: Invalid animacy_name: expected 'Одушевлённое' or 'Неодушевлённое'."
        ]
        assert not Word.objects.exists()


class TestImportContextsEndpoint:
    url = "/api/import/contexts/"

    def test_successful_import(self, auth_client, db):
        csv_content = "text\nя живу в ____\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 200
        assert response.data["created"] == 1
        assert Context.objects.filter(text="я живу в ____").exists()

    def test_rejects_context_without_placeholder(self, auth_client, db):
        csv_content = "text\nбез пропуска\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0

    def test_rejects_context_with_two_placeholders(self, auth_client, db):
        csv_content = "text\nЭтот ____ очень ____\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0

    def test_context_text_casing_is_preserved_on_import(self, auth_client, db):
        """Import must NOT lowercase the context text.

        The API path (ContextSerializer) preserves case; the import path
        must behave the same way so a context created via API and via
        import are identical.
        """
        csv_content = "text\nВ ____ живёт семья\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 200
        assert response.data["created"] == 1
        from language_trainer_app.models.context import Context

        assert Context.objects.filter(text="В ____ живёт семья").exists()
        assert not Context.objects.filter(text="в ____ живёт семья").exists()


class TestImportWordFormsEndpoint:
    url = "/api/import/word-forms/"

    def test_successful_import(self, auth_client, reference_data):
        rd = reference_data
        Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        csv_content = (
            "word_base_form,word_part_of_speech_name,word_gender_name,"
            "word_form,case_name,form_gender_name,number_name\n"
            "дом,существительное,мужской,дом,именительный,,единственное\n"
        )
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 200
        assert response.data["created"] == 1

    def test_error_when_word_not_found(self, auth_client, reference_data):
        csv_content = (
            "word_base_form,word_part_of_speech_name,word_gender_name,"
            "word_form,case_name,form_gender_name,number_name\n"
            "несуществующий,существительное,мужской,дом,именительный,,единственное\n"
        )
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0
