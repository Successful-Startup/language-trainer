import random
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
        """Get ContextWordFormPair queryset filtered by test parameters."""
        query = ContextWordFormPair.objects.filter(
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
            query = query.filter(
                adjective_form__isnull=False,
                adjective_form__gender__in=genders,
                adjective_form__case__in=cases,
                adjective_form__number__in=numbers,
            )
        else:
            query = query.filter(adjective_form__isnull=True)

        return query

    def generate_test(self, test_params: TestParameters) -> TestItem:
        """Generate a single test item based on parameters."""
        word_form_pairs = self._get_pairs_by_params(
            use_adjective=test_params.use_adjective,
            genders=test_params.genders,
            cases=test_params.cases,
            numbers=test_params.numbers,
        )

        word_form_pairs_list = list(word_form_pairs)
        if not word_form_pairs_list:
            raise ValueError(
                "No matching word form pairs found for the given parameters"
            )

        selected_pair = random.choice(word_form_pairs_list)
        return self._build_test_item(selected_pair, test_params.use_adjective)

    def generate_tests(
        self, test_params: TestParameters, count: int = 10
    ) -> List[TestItem]:
        """Generate multiple test items based on parameters, up to the specified count."""
        word_form_pairs = self._get_pairs_by_params(
            use_adjective=test_params.use_adjective,
            genders=test_params.genders,
            cases=test_params.cases,
            numbers=test_params.numbers,
        )

        word_form_pairs_list = list(word_form_pairs)

        if not word_form_pairs_list:
            return []

        actual_count = min(count, len(word_form_pairs_list))
        selected_pairs = random.sample(word_form_pairs_list, actual_count)

        return [
            self._build_test_item(pair, test_params.use_adjective)
            for pair in selected_pairs
        ]

    def _build_test_item(self, pair, use_adjective: bool) -> TestItem:
        """Build a TestItem from a ContextWordFormPair."""
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
