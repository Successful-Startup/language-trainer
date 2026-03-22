"""Tests for TestGeneratorService."""

import pytest

from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.test_item import TestItem
from language_trainer_app.models.test_parameters import TestParameters
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.services.test_generator_service import TestGeneratorService


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
