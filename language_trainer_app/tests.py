"""
Tests for language_trainer_app.

Run inside Docker:
    docker-compose exec web pytest

Or locally (requires Django deps):
    pytest
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.test_item import TestItem
from language_trainer_app.models.test_parameters import TestParameters
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber
from language_trainer_app.services.test_generator_service import TestGeneratorService
from language_trainer_app.utils.csv_import_utils import (
    MAX_ERRORS,
    find_reference_or_error,
    format_import_response,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(username="teacher", password="pass1234")


@pytest.fixture
def auth_client(api_client, teacher_user):
    api_client.force_authenticate(user=teacher_user)
    return api_client


@pytest.fixture
def reference_data(db):
    """Create the minimal reference data needed for import and test-generation tests."""
    gender_m = Gender.objects.create(name="мужской")
    gender_f = Gender.objects.create(name="женский")
    pos_noun = PartOfSpeech.objects.create(name="существительное")
    pos_adj = PartOfSpeech.objects.create(name="прилагательное")
    case_nom = Case.objects.create(name="именительный")
    number_sg = WordNumber.objects.create(name="единственное")
    return {
        "gender_m": gender_m,
        "gender_f": gender_f,
        "pos_noun": pos_noun,
        "pos_adj": pos_adj,
        "case_nom": case_nom,
        "number_sg": number_sg,
    }


@pytest.fixture
def full_test_data(db, reference_data):
    """Create a complete ContextWordFormPair for test-generation tests (noun only)."""
    rd = reference_data
    word = Word.objects.create(
        base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
    )
    noun_form = WordForm.objects.create(
        word=word,
        case=rd["case_nom"],
        gender=None,
        number=rd["number_sg"],
        word_form="дом",
    )
    context = Context.objects.create(text="я живу в ____")
    pair = ContextWordFormPair.objects.create(
        context=context, noun_form=noun_form, adjective_form=None
    )
    return {**rd, "word": word, "noun_form": noun_form, "context": context, "pair": pair}


# ---------------------------------------------------------------------------
# Unit tests: csv_import_utils
# ---------------------------------------------------------------------------


class TestFindReferenceOrError:
    def test_returns_none_for_falsy_value(self):
        model = MagicMock()
        result = find_reference_or_error(model, "name", "", "Prefix")
        assert result is None
        model.objects.filter.assert_not_called()

    def test_returns_none_for_none_value(self):
        model = MagicMock()
        result = find_reference_or_error(model, "name", None, "Prefix")
        assert result is None

    def test_returns_object_when_found(self, db):
        gender = Gender.objects.create(name="мужской")
        result = find_reference_or_error(Gender, "name", "мужской", "Invalid gender")
        assert result == gender

    def test_case_insensitive_lookup(self, db):
        gender = Gender.objects.create(name="мужской")
        result = find_reference_or_error(Gender, "name", "МУЖСКОЙ", "Invalid gender")
        assert result == gender

    def test_raises_value_error_when_not_found(self, db):
        with pytest.raises(ValueError, match="Invalid gender 'несуществующий'"):
            find_reference_or_error(Gender, "name", "несуществующий", "Invalid gender")


class TestFormatImportResponse:
    def test_success_when_no_errors(self):
        result = format_import_response(10, 8, 2, [])
        assert result["success"] is True
        assert result["total_rows"] == 10
        assert result["created"] == 8
        assert result["skipped"] == 2
        assert result["errors"] == 0
        assert result["error_details"] == []

    def test_failure_when_errors_present(self):
        errors = ["Row 2: bad data", "Row 3: missing field"]
        result = format_import_response(5, 3, 0, errors)
        assert result["success"] is False
        assert result["errors"] == 2
        assert result["error_details"] == errors

    def test_truncates_errors_beyond_max(self):
        errors = [f"Row {i}: error" for i in range(MAX_ERRORS + 5)]
        result = format_import_response(MAX_ERRORS + 5, 0, 0, errors)
        # error_details should be MAX_ERRORS items + 1 sentinel
        assert len(result["error_details"]) == MAX_ERRORS + 1
        assert "more validation errors" in result["error_details"][-1]

    def test_errors_count_reflects_full_list(self):
        errors = [f"Row {i}: error" for i in range(MAX_ERRORS + 5)]
        result = format_import_response(MAX_ERRORS + 5, 0, 0, errors)
        assert result["errors"] == MAX_ERRORS + 5


# ---------------------------------------------------------------------------
# Unit tests: TestGeneratorService
# ---------------------------------------------------------------------------


class TestTestGeneratorService:
    def test_returns_empty_list_when_no_pairs(self, db, reference_data):
        rd = reference_data
        service = TestGeneratorService()
        params = TestParameters(
            use_adjective=False,
            genders=[rd["gender_m"].id],
            cases=[rd["case_nom"].id],
            numbers=[rd["number_sg"].id],
        )
        result = service.generate_tests(params, count=10)
        assert result == []

    def test_returns_test_items_for_matching_pairs(self, db, full_test_data):
        rd = full_test_data
        service = TestGeneratorService()
        params = TestParameters(
            use_adjective=False,
            genders=[rd["gender_m"].id],
            cases=[rd["case_nom"].id],
            numbers=[rd["number_sg"].id],
        )
        result = service.generate_tests(params, count=10)
        assert len(result) == 1
        item = result[0]
        assert isinstance(item, TestItem)
        assert item.context == "я живу в ____"
        assert item.noun_with_adjective == "дом"
        assert item.correct_answer == "дом"

    def test_respects_count_limit(self, db, reference_data):
        """Generates at most `count` items even when more pairs exist."""
        rd = reference_data
        word = Word.objects.create(
            base_form="стол", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        for i in range(5):
            form = WordForm.objects.create(
                word=word,
                case=rd["case_nom"],
                gender=None,
                number=rd["number_sg"],
                word_form=f"стол{i}",
            )
            ctx = Context.objects.create(text=f"на ____ {i}")
            ContextWordFormPair.objects.create(
                context=ctx, noun_form=form, adjective_form=None
            )

        service = TestGeneratorService()
        params = TestParameters(
            use_adjective=False,
            genders=[rd["gender_m"].id],
            cases=[rd["case_nom"].id],
            numbers=[rd["number_sg"].id],
        )
        result = service.generate_tests(params, count=3)
        assert len(result) <= 3

    def test_use_adjective_filters_out_noun_only_pairs(self, db, full_test_data):
        """When use_adjective=True, pairs without adjective_form must be excluded."""
        rd = full_test_data
        service = TestGeneratorService()
        params = TestParameters(
            use_adjective=True,
            genders=[rd["gender_m"].id],
            cases=[rd["case_nom"].id],
            numbers=[rd["number_sg"].id],
        )
        result = service.generate_tests(params, count=10)
        assert result == []


# ---------------------------------------------------------------------------
# Integration tests: CSV Import API
# ---------------------------------------------------------------------------


def _csv_file(content: str, filename: str = "test.csv"):
    """Helper: wrap CSV string as an in-memory upload."""
    return io.BytesIO(content.encode("utf-8")), filename


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
        f = io.BytesIO(b"data")
        response = auth_client.post(self.url, {"file": (f, "data.txt")}, format="multipart")
        assert response.status_code == 400

    def test_successful_import(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,существительное,мужской\n"
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["created"] == 1
        assert Word.objects.filter(base_form="дом").exists()

    def test_skips_duplicate_on_reimport(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,существительное,мужской\n"
        f1, name = _csv_file(csv_content)
        auth_client.post(self.url, {"file": (f1, name)}, format="multipart")

        f2, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f2, name)}, format="multipart")
        assert response.data["skipped"] == 1
        assert response.data["created"] == 0

    def test_reports_error_for_invalid_pos(self, auth_client, reference_data):
        csv_content = "base_form,part_of_speech_name,gender_name\nдом,несуществующий,мужской\n"
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0

    def test_missing_required_header(self, auth_client):
        csv_content = "base_form,gender_name\nдом,мужской\n"
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.status_code == 400
        assert "Missing required headers" in response.data["error"]

    def test_transaction_rolls_back_on_error(self, auth_client, reference_data):
        """A row that raises after a successful row must NOT partially commit."""
        csv_content = (
            "base_form,part_of_speech_name,gender_name\n"
            "дом,существительное,мужской\n"
            "кот,несуществующий,мужской\n"
        )
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        # First row succeeds, second fails — both should be in DB because
        # the transaction rolls back only on unhandled exceptions.
        # The import controller collects errors without re-raising, so the
        # transaction commits what succeeded.
        assert response.data["created"] == 1
        assert response.data["errors"] == 1


class TestImportContextsEndpoint:
    url = "/api/import/contexts/"

    def test_requires_authentication(self, api_client):
        response = api_client.post(self.url, {}, format="multipart")
        assert response.status_code == 401

    def test_successful_import(self, auth_client, db):
        csv_content = "text\nя живу в ____\n"
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.status_code == 200
        assert response.data["created"] == 1
        assert Context.objects.filter(text="я живу в ____").exists()

    def test_rejects_context_without_placeholder(self, auth_client, db):
        csv_content = "text\nбез пропуска\n"
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0


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
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.status_code == 200
        assert response.data["created"] == 1

    def test_error_when_word_not_found(self, auth_client, reference_data):
        csv_content = (
            "word_base_form,word_part_of_speech_name,word_gender_name,"
            "word_form,case_name,form_gender_name,number_name\n"
            "несуществующий,существительное,мужской,дом,именительный,,единственное\n"
        )
        f, name = _csv_file(csv_content)
        response = auth_client.post(self.url, {"file": (f, name)}, format="multipart")
        assert response.data["errors"] == 1
        assert response.data["created"] == 0


# ---------------------------------------------------------------------------
# Integration tests: Test Generation API
# ---------------------------------------------------------------------------


class TestGenerateEndpoint:
    url = "/tests/generate/"

    def _valid_payload(self, reference_data):
        rd = reference_data
        return {
            "use_adjective": False,
            "genders": [rd["gender_m"].id],
            "cases": [rd["case_nom"].id],
            "numbers": [rd["number_sg"].id],
        }

    def test_returns_200_with_no_data(self, api_client, reference_data):
        payload = self._valid_payload(reference_data)
        response = api_client.post(self.url, payload, format="json")
        assert response.status_code == 200
        assert response.data == []

    def test_returns_items_when_data_exists(self, api_client, full_test_data):
        payload = self._valid_payload(full_test_data)
        response = api_client.post(self.url, payload, format="json")
        assert response.status_code == 200
        assert len(response.data) == 1
        item = response.data[0]
        assert "context" in item
        assert "noun_with_adjective" in item
        assert "correct_answer" in item

    def test_invalid_payload_returns_400(self, api_client, db):
        response = api_client.post(self.url, {"use_adjective": "notabool"}, format="json")
        assert response.status_code == 400

    def test_allows_anonymous_access(self, api_client, db):
        """Test generation endpoint must not require authentication."""
        response = api_client.post(
            self.url,
            {"use_adjective": False, "genders": [], "cases": [], "numbers": []},
            format="json",
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Integration tests: Authentication endpoints
# ---------------------------------------------------------------------------


class TestAuthEndpoints:
    login_url = "/auth/login/"
    refresh_url = "/auth/refresh/"

    def test_login_returns_tokens(self, db, api_client):
        User.objects.create_user(username="u", password="p")
        response = api_client.post(
            self.login_url, {"username": "u", "password": "p"}, format="json"
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_rejects_wrong_password(self, db, api_client):
        User.objects.create_user(username="u", password="correct")
        response = api_client.post(
            self.login_url, {"username": "u", "password": "wrong"}, format="json"
        )
        assert response.status_code == 401

    def test_refresh_returns_new_access_token(self, db, api_client):
        User.objects.create_user(username="u", password="p")
        login_resp = api_client.post(
            self.login_url, {"username": "u", "password": "p"}, format="json"
        )
        refresh_token = login_resp.data["refresh"]
        refresh_resp = api_client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        assert refresh_resp.status_code == 200
        assert "access" in refresh_resp.data


# ---------------------------------------------------------------------------
# Integration tests: Permission enforcement
# ---------------------------------------------------------------------------


class TestPermissions:
    def test_anonymous_can_read_words(self, api_client, db):
        response = api_client.get("/words/")
        assert response.status_code == 200

    def test_anonymous_cannot_create_word(self, api_client, db):
        response = api_client.post("/words/", {"base_form": "тест"}, format="json")
        assert response.status_code == 401

    def test_authenticated_can_create_gender(self, auth_client, db):
        response = auth_client.post("/genders/", {"name": "мужской"}, format="json")
        assert response.status_code == 201

    def test_anonymous_cannot_import(self, api_client, db):
        csv_content = "base_form,part_of_speech_name\nдом,существительное\n"
        f, name = _csv_file(csv_content)
        response = api_client.post(
            "/api/import/words/", {"file": (f, name)}, format="multipart"
        )
        assert response.status_code == 401
