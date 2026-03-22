"""Integration tests for CSV import API endpoints."""

import pytest

from language_trainer_app.models.context import Context
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.tests.conftest import make_csv_file


class TestImportWordsEndpoint:
    url = "/api/import/words/"

    def test_requires_authentication(self, api_client):
        response = api_client.post(self.url, {}, format="multipart")
        assert response.status_code == 401

    def test_rejects_missing_file(self, auth_client):
        response = auth_client.post(self.url, {}, format="multipart")
        assert response.status_code == 400
        assert "No file provided" in response.data["error"]

    def test_rejects_non_csv_file(self, auth_client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        f = SimpleUploadedFile("data.txt", b"data", content_type="text/plain")
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 400

    def test_successful_import(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,существительное,мужской\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["created"] == 1
        assert Word.objects.filter(base_form="дом").exists()

    def test_skips_duplicate_on_reimport(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,существительное,мужской\n"
        auth_client.post(self.url, {"file": make_csv_file(csv_content)}, format="multipart")

        response = auth_client.post(
            self.url, {"file": make_csv_file(csv_content)}, format="multipart"
        )
        assert response.data["skipped"] == 1
        assert response.data["created"] == 0

    def test_reports_error_for_invalid_pos(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,несуществующий,мужской\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0

    def test_missing_required_header(self, auth_client):
        csv_content = "base_form,gender_name\nдом,мужской\n"
        f = make_csv_file(csv_content)
        response = auth_client.post(self.url, {"file": f}, format="multipart")
        assert response.status_code == 400
        assert "Missing required headers" in response.data["error"]

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


class TestImportContextsEndpoint:
    url = "/api/import/contexts/"

    def test_requires_authentication(self, api_client):
        response = api_client.post(self.url, {}, format="multipart")
        assert response.status_code == 401

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

    def test_requires_authentication(self, api_client):
        response = api_client.post(self.url, {}, format="multipart")
        assert response.status_code == 401

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
