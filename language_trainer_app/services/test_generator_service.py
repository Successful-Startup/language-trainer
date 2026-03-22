from typing import List

from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.test_item import TestItem
from language_trainer_app.models.test_parameters import TestParameters


class TestGeneratorService:
    """Service for generating language learning tests."""

    def _get_pairs_by_params(
        self,
        use_adjective: bool,
        genders: List[int],
        cases: List[int],
        numbers: List[int],
    ):
        """Return a ContextWordFormPair queryset filtered by test parameters."""
        queryset = ContextWordFormPair.objects.filter(
            noun_form__gender__in=genders,
            noun_form__case__in=cases,
            noun_form__number__in=numbers,
        ).select_related(
            "context",
            "noun_form",
            "noun_form__word",
            "adjective_form",
            "adjective_form__word",
        )

        if use_adjective:
            queryset = queryset.filter(
                adjective_form__isnull=False,
                adjective_form__gender__in=genders,
                adjective_form__case__in=cases,
                adjective_form__number__in=numbers,
            )
        else:
            queryset = queryset.filter(adjective_form__isnull=True)

        return queryset

    def generate_tests(
        self, test_params: TestParameters, count: int = 10
    ) -> List[TestItem]:
        """Generate up to *count* random test items for the given parameters.

        Random selection is pushed to the database via ORDER BY RANDOM() so
        that no unnecessary rows are transferred to Python.
        """
        pairs = self._get_pairs_by_params(
            use_adjective=test_params.use_adjective,
            genders=test_params.genders,
            cases=test_params.cases,
            numbers=test_params.numbers,
        ).order_by("?")[:count]

        return [
            self._build_test_item(pair, test_params.use_adjective) for pair in pairs
        ]

    def _build_test_item(self, pair: ContextWordFormPair, use_adjective: bool) -> TestItem:
        """Build a TestItem DTO from a ContextWordFormPair instance."""
        context = pair.context.text

        if use_adjective:
            noun_with_adjective = (
                f"{pair.adjective_form.word.base_form} {pair.noun_form.word.base_form}"
            )
            correct_answer = (
                f"{pair.adjective_form.word_form} {pair.noun_form.word_form}"
            )
        else:
            noun_with_adjective = pair.noun_form.word.base_form
            correct_answer = pair.noun_form.word_form

        return TestItem(
            context=context,
            noun_with_adjective=noun_with_adjective,
            correct_answer=correct_answer,
        )
