"""Integration tests for test-generation API, auth endpoints, and permissions."""

import pytest
from django.contrib.auth.models import User

from language_trainer_app.tests.conftest import make_csv_file


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

    def test_allows_anonymous_access(self, api_client, reference_data):
        """Test generation endpoint must not require authentication."""
        rd = reference_data
        response = api_client.post(
            self.url,
            {
                "use_adjective": False,
                "genders": [rd["gender_m"].id],
                "cases": [rd["case_nom"].id],
                "numbers": [rd["number_sg"].id],
            },
            format="json",
        )
        assert response.status_code == 200


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
        f = make_csv_file("base_form,part_of_speech_name\nдом,существительное\n")
        response = api_client.post(
            "/api/import/words/", {"file": f}, format="multipart"
        )
        assert response.status_code == 401
