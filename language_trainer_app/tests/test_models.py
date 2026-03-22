"""Tests for model-level constraint behavior."""

import pytest
from django.db import IntegrityError

from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm


class TestWordNullGenderUniqueness:
    """
    Word has a UniqueConstraint on (base_form, part_of_speech, gender).
    When gender IS NULL, PostgreSQL treats NULL != NULL in regular unique
    indexes, so without a partial constraint two Words with the same
    (base_form, part_of_speech) and gender=NULL can coexist.

    The correct fix: two partial UniqueConstraints (one for IS NULL, one
    for IS NOT NULL), matching the pattern used in ContextWordFormPair.
    """

    def test_duplicate_word_with_non_null_gender_raises(self, db, reference_data):
        """Sanity check: duplicate (base_form, pos, non-null gender) is rejected."""
        rd = reference_data
        Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        with pytest.raises(IntegrityError):
            Word.objects.create(
                base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
            )

    def test_duplicate_word_with_null_gender_raises(self, db, reference_data):
        """Two Words with the same (base_form, pos) and gender=NULL must be rejected."""
        rd = reference_data
        Word.objects.create(
            base_form="идти", part_of_speech=rd["pos_noun"], gender=None
        )
        with pytest.raises(IntegrityError):
            Word.objects.create(
                base_form="идти", part_of_speech=rd["pos_noun"], gender=None
            )

    def test_word_with_null_gender_and_non_null_gender_are_different(
        self, db, reference_data
    ):
        """(base_form, pos, NULL) and (base_form, pos, gender) are distinct — both allowed."""
        rd = reference_data
        Word.objects.create(
            base_form="идти", part_of_speech=rd["pos_noun"], gender=None
        )
        # Different gender — should not raise
        Word.objects.create(
            base_form="идти", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        assert Word.objects.filter(base_form="идти").count() == 2


class TestWordFormNullGenderUniqueness:
    """
    WordForm has a UniqueConstraint on (word, case, gender, number).
    Same NULL-uniqueness bug as Word: two WordForms with gender=NULL and
    the same other fields should be rejected but currently are not.
    """

    def test_duplicate_word_form_with_non_null_gender_raises(self, db, reference_data):
        """Sanity check: duplicate (word, case, non-null gender, number) is rejected."""
        rd = reference_data
        word = Word.objects.create(
            base_form="красивый", part_of_speech=rd["pos_adj"], gender=rd["gender_m"]
        )
        WordForm.objects.create(
            word=word,
            case=rd["case_nom"],
            gender=rd["gender_m"],
            number=rd["number_sg"],
            word_form="красивый",
        )
        with pytest.raises(IntegrityError):
            WordForm.objects.create(
                word=word,
                case=rd["case_nom"],
                gender=rd["gender_m"],
                number=rd["number_sg"],
                word_form="красивый",
            )

    def test_duplicate_word_form_with_null_gender_raises(self, db, reference_data):
        """Two WordForms with same (word, case, number) and gender=NULL must be rejected."""
        rd = reference_data
        word = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        WordForm.objects.create(
            word=word,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дом",
        )
        with pytest.raises(IntegrityError):
            WordForm.objects.create(
                word=word,
                case=rd["case_nom"],
                gender=None,
                number=rd["number_sg"],
                word_form="дом2",
            )

    def test_word_form_with_null_and_non_null_gender_are_different(
        self, db, reference_data
    ):
        """(word, case, NULL, number) and (word, case, gender, number) are distinct."""
        rd = reference_data
        word = Word.objects.create(
            base_form="дом", part_of_speech=rd["pos_noun"], gender=rd["gender_m"]
        )
        WordForm.objects.create(
            word=word,
            case=rd["case_nom"],
            gender=None,
            number=rd["number_sg"],
            word_form="дом",
        )
        # Different gender — should not raise
        WordForm.objects.create(
            word=word,
            case=rd["case_nom"],
            gender=rd["gender_m"],
            number=rd["number_sg"],
            word_form="дома",
        )
        assert WordForm.objects.filter(word=word).count() == 2
