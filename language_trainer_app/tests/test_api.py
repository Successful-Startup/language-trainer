"""Integration tests for test-generation API, auth endpoints, and permissions."""

import pytest
from django.contrib.auth.models import User

from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
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
        response = api_client.post(
            self.url, {"use_adjective": "notabool"}, format="json"
        )
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


class TestWordSearch:
    url = "/words/"

    @pytest.fixture(autouse=True)
    def setup_words(self, reference_data):
        rd = reference_data
        self.word_dom = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.word_dom2 = Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.word_koshka = Word.objects.create(
            base_form="кошка", part_of_speech=rd["pos_noun"], gender=rd["gender_f"]
        )

    def test_search_returns_matching_words(self, api_client):
        response = api_client.get(self.url, {"search": "дом"})
        assert response.status_code == 200
        results = response.data["results"]
        base_forms = [w["base_form"] for w in results]
        assert "дом" in base_forms
        assert "домик" in base_forms
        assert "кошка" not in base_forms

    def test_search_empty_returns_all(self, api_client):
        response = api_client.get(self.url, {"search": ""})
        assert response.status_code == 200
        assert response.data["count"] >= 3

    def test_search_no_match_returns_empty(self, api_client):
        response = api_client.get(self.url, {"search": "zzz_no_match_zzz"})
        assert response.status_code == 200
        assert response.data["results"] == []


class TestWordExactSearch:
    url = "/words/"

    @pytest.fixture(autouse=True)
    def setup_words(self, reference_data):
        rd = reference_data
        self.word_dom_noun = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.word_dom_adjective = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_adj"], gender=rd["gender_m"]
        )
        Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )

    def test_exact_search_returns_only_full_matches(self, api_client):
        response = api_client.get(self.url, {"search": "дом", "match": "exact"})
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 2
        assert {word["base_form"] for word in results} == {"дом"}

    def test_exact_search_is_case_insensitive(self, api_client):
        response = api_client.get(self.url, {"search": "ДОМ", "match": "exact"})
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 2
        assert {word["base_form"] for word in results} == {"дом"}

    def test_exact_search_supports_part_of_speech_filter(
        self, api_client, reference_data
    ):
        response = api_client.get(
            self.url,
            {
                "search": "дом",
                "match": "exact",
                "part_of_speech": reference_data["pos_noun"].id,
            },
        )
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["base_form"] == "дом"
        assert results[0]["part_of_speech"] == reference_data["pos_noun"].id


class TestWordFormSearch:
    url = "/word-forms/"

    @pytest.fixture(autouse=True)
    def setup_word_forms(self, reference_data):
        rd = reference_data
        word = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.form_dom = WordForm.objects.create(
            word=word,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дому",
        )
        word2 = Word.objects.create(
            base_form="кошка", part_of_speech=rd["pos_noun"], gender=rd["gender_f"]
        )
        self.form_koshka = WordForm.objects.create(
            word=word2,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="кошке",
        )

    def test_search_by_word_form_returns_match(self, api_client):
        response = api_client.get(self.url, {"search": "дому"})
        assert response.status_code == 200
        results = response.data["results"]
        word_forms = [wf["word_form"] for wf in results]
        assert "дому" in word_forms
        assert "кошке" not in word_forms

    def test_search_by_base_form_returns_match(self, api_client):
        response = api_client.get(self.url, {"search": "кошка"})
        assert response.status_code == 200
        results = response.data["results"]
        word_forms = [wf["word_form"] for wf in results]
        assert "кошке" in word_forms
        assert "дому" not in word_forms

    def test_search_empty_returns_all(self, api_client):
        response = api_client.get(self.url, {"search": ""})
        assert response.status_code == 200
        assert response.data["count"] >= 2

    def test_search_no_match_returns_empty(self, api_client):
        response = api_client.get(self.url, {"search": "zzz_no_match_zzz"})
        assert response.status_code == 200
        assert response.data["results"] == []


class TestWordFormExactSearch:
    url = "/word-forms/"

    @pytest.fixture(autouse=True)
    def setup_word_forms(self, reference_data):
        rd = reference_data
        noun_word = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        adjective_word = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_adj"], gender=rd["gender_m"]
        )
        other_word = Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )

        self.noun_form = WordForm.objects.create(
            word=noun_word,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дом",
        )
        self.adjective_form = WordForm.objects.create(
            word=adjective_word,
            case=rd["case_nom"],
            gender=rd["gender_m"],
            number=rd["number_sg"],
            word_form="дом",
        )
        WordForm.objects.create(
            word=other_word,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="домик",
        )

    def test_exact_search_returns_only_full_word_form_matches(self, api_client):
        response = api_client.get(self.url, {"search": "дом", "match": "exact"})
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 2
        assert {word_form["word_form"] for word_form in results} == {"дом"}

    def test_exact_search_is_case_insensitive(self, api_client):
        response = api_client.get(self.url, {"search": "ДОМ", "match": "exact"})
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 2
        assert {word_form["word_form"] for word_form in results} == {"дом"}

    def test_exact_search_supports_word_part_of_speech_filter(
        self, api_client, reference_data
    ):
        response = api_client.get(
            self.url,
            {
                "search": "дом",
                "match": "exact",
                "word_part_of_speech": reference_data["pos_adj"].id,
            },
        )
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["word_form"] == "дом"
        assert results[0]["word"]["part_of_speech"] == reference_data["pos_adj"].id


class TestWordSearchRanking:
    """Exact match must come first, then startswith, then contains."""

    url = "/words/"

    @pytest.fixture(autouse=True)
    def setup_words(self, reference_data):
        rd = reference_data
        Word.objects.create(
            base_form="бездомник", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )

    def test_exact_match_comes_first(self, api_client):
        response = api_client.get(self.url, {"search": "дом"})
        assert response.status_code == 200
        base_forms = [w["base_form"] for w in response.data["results"]]
        assert base_forms[0] == "дом"

    def test_startswith_before_contains(self, api_client):
        response = api_client.get(self.url, {"search": "дом"})
        assert response.status_code == 200
        base_forms = [w["base_form"] for w in response.data["results"]]
        assert base_forms.index("домик") < base_forms.index("бездомник")

    def test_ranking_without_exact_match(self, api_client):
        """When no exact match exists, startswith still comes before contains."""
        response = api_client.get(self.url, {"search": "доми"})
        assert response.status_code == 200
        base_forms = [w["base_form"] for w in response.data["results"]]
        assert base_forms == ["домик"]


class TestWordFormSearchRanking:
    """word_form exact/startswith ranks above word__base_form matches."""

    url = "/word-forms/"

    @pytest.fixture(autouse=True)
    def setup_forms(self, reference_data):
        rd = reference_data
        word_dom = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        word_domik = Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        word_bezdom = Word.objects.create(
            base_form="бездомник", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        # word_form exact match: "дом"
        WordForm.objects.create(
            word=word_dom,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дом",
        )
        # word_form startswith "дом": "домой"
        WordForm.objects.create(
            word=word_domik,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="домой",
        )
        # word_form matched via base_form only (contains "дом" in base_form)
        WordForm.objects.create(
            word=word_bezdom,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="бездомнику",
        )

    def test_exact_word_form_match_comes_first(self, api_client):
        response = api_client.get(self.url, {"search": "дом"})
        assert response.status_code == 200
        forms = [wf["word_form"] for wf in response.data["results"]]
        assert forms[0] == "дом"

    def test_startswith_word_form_before_base_form_match(self, api_client):
        response = api_client.get(self.url, {"search": "дом"})
        assert response.status_code == 200
        forms = [wf["word_form"] for wf in response.data["results"]]
        assert forms.index("домой") < forms.index("бездомнику")


class TestWordFormExactSearchByBaseForm:
    """Exact search with search_field=base_form returns all forms of the base word."""

    url = "/word-forms/"

    @pytest.fixture(autouse=True)
    def setup_word_forms(self, reference_data):
        rd = reference_data
        self.word_dom = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.word_domik = Word.objects.create(
            base_form="домик", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        self.word_dom_adj = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_adj"], gender=rd["gender_m"]
        )

        # Multiple forms of "дом" noun
        self.form_dom_nom = WordForm.objects.create(
            word=self.word_dom,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дом",
        )
        self.form_dom_gen = WordForm.objects.create(
            word=self.word_dom,
            case=rd["case_gen"],
            gender=None,
            number=rd["number_sg"],
            word_form="дома",
        )
        self.form_dom_dat = WordForm.objects.create(
            word=self.word_dom,
            case=rd["case_dat"],
            gender=None,
            number=rd["number_sg"],
            word_form="дому",
        )
        # Form of "домик" — should NOT appear in exact base_form search for "дом"
        self.form_domik = WordForm.objects.create(
            word=self.word_domik,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="домик",
        )
        # Form of "дом" adjective
        self.form_dom_adj = WordForm.objects.create(
            word=self.word_dom_adj,
            case=rd["case_nom"],
            gender=rd["gender_m"],
            number=rd["number_sg"],
            word_form="домовый",
        )

    def test_base_form_search_returns_all_forms_of_exact_word(self, api_client):
        """search_field=base_form + match=exact returns ALL forms of word 'дом'."""
        response = api_client.get(
            self.url,
            {"search": "дом", "match": "exact", "search_field": "base_form"},
        )
        assert response.status_code == 200
        results = response.data["results"]
        word_forms = {wf["word_form"] for wf in results}
        # All forms of base_form=дом must be present
        assert "дом" in word_forms
        assert "дома" in word_forms
        assert "дому" in word_forms
        assert "домовый" in word_forms
        # Forms of base_form=домик must NOT be present
        assert "домик" not in word_forms

    def test_base_form_search_is_case_insensitive(self, api_client):
        response = api_client.get(
            self.url,
            {"search": "ДОМ", "match": "exact", "search_field": "base_form"},
        )
        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 4  # дом, дома, дому, домовый

    def test_base_form_search_with_pos_filter(self, api_client, reference_data):
        """Combining search_field=base_form with word_part_of_speech narrows results."""
        response = api_client.get(
            self.url,
            {
                "search": "дом",
                "match": "exact",
                "search_field": "base_form",
                "word_part_of_speech": reference_data["pos_noun"].id,
            },
        )
        assert response.status_code == 200
        results = response.data["results"]
        # Only noun forms: дом, дома, дому (not домовый which is adjective)
        assert len(results) == 3
        word_forms = {wf["word_form"] for wf in results}
        assert word_forms == {"дом", "дома", "дому"}

    def test_base_form_search_no_match_returns_empty(self, api_client):
        response = api_client.get(
            self.url,
            {"search": "zzz", "match": "exact", "search_field": "base_form"},
        )
        assert response.status_code == 200
        assert response.data["results"] == []

    def test_default_exact_search_still_works_by_word_form(self, api_client):
        """Without search_field, exact search continues filtering by word_form."""
        response = api_client.get(self.url, {"search": "дом", "match": "exact"})
        assert response.status_code == 200
        results = response.data["results"]
        # Only forms where word_form == 'дом' exactly
        assert len(results) == 1
        assert results[0]["word_form"] == "дом"
