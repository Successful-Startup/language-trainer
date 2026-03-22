"""N+1 query regression tests for list endpoints.

Each test asserts that fetching a list of N objects generates a fixed
(small) number of DB queries regardless of N, proving that no N+1 query
problem exists for that endpoint.

We use pytest-django's ``django_assert_num_queries`` context manager to
assert the exact query count.  If a future refactoring breaks
``select_related`` the count will rise above the constant and these
tests will catch it.
"""

from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm


class TestWordFormListQueries:
    """GET /word-forms/ must not issue N extra queries per word form."""

    url = "/word-forms/"

    def _make_word_forms(self, reference_data, count):
        rd = reference_data
        forms = []
        for i in range(count):
            word = Word.objects.create(
                base_form=f"слово{i}",
                part_of_speech=rd["pos_noun"],
                gender=rd["gender_m"],
            )
            wf = WordForm.objects.create(
                word=word,
                case=rd["case_nom"],
                gender=None,
                number=rd["number_sg"],
                word_form=f"слово{i}",
            )
            forms.append(wf)
        return forms

    def test_single_item_query_count(
        self, api_client, reference_data, django_assert_num_queries
    ):
        self._make_word_forms(reference_data, 1)
        with django_assert_num_queries(2):
            # 1: COUNT(*) for pagination
            # 2: SELECT word_forms JOIN word JOIN ... (select_related)
            response = api_client.get(self.url)
        assert response.status_code == 200

    def test_multiple_items_same_query_count(
        self, api_client, reference_data, django_assert_num_queries
    ):
        """Doubling the number of rows must NOT increase the query count."""
        self._make_word_forms(reference_data, 5)
        with django_assert_num_queries(2):
            response = api_client.get(self.url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 5


class TestContextWordFormPairListQueries:
    """GET /context-word-form-pairs/ must not issue N extra queries per pair."""

    url = "/context-word-form-pairs/"

    def _make_pairs(self, reference_data, count):
        rd = reference_data
        pairs = []
        for i in range(count):
            word = Word.objects.create(
                base_form=f"слово{i}",
                part_of_speech=rd["pos_noun"],
                gender=rd["gender_m"],
            )
            noun_form = WordForm.objects.create(
                word=word,
                case=rd["case_nom"],
                gender=None,
                number=rd["number_sg"],
                word_form=f"слово{i}",
            )
            context = Context.objects.create(text=f"В ____ {i} живёт семья")
            pair = ContextWordFormPair.objects.create(
                context=context,
                noun_form=noun_form,
                adjective_form=None,
            )
            pairs.append(pair)
        return pairs

    def test_single_item_query_count(
        self, api_client, reference_data, django_assert_num_queries
    ):
        self._make_pairs(reference_data, 1)
        with django_assert_num_queries(2):
            # 1: COUNT(*) for pagination
            # 2: SELECT ... with all select_related joins
            response = api_client.get(self.url)
        assert response.status_code == 200

    def test_multiple_items_same_query_count(
        self, api_client, reference_data, django_assert_num_queries
    ):
        """Doubling the number of rows must NOT increase the query count."""
        self._make_pairs(reference_data, 5)
        with django_assert_num_queries(2):
            response = api_client.get(self.url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
