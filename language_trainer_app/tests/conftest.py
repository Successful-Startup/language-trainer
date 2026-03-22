"""
Shared fixtures and helpers for language_trainer_app tests.
"""

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber


# ---------------------------------------------------------------------------
# Helpers (plain functions, not fixtures)
# ---------------------------------------------------------------------------


def make_csv_file(content: str, filename: str = "test.csv") -> SimpleUploadedFile:
    """Wrap a CSV string as a SimpleUploadedFile (mimics a real upload)."""
    return SimpleUploadedFile(filename, content.encode("utf-8"), content_type="text/csv")


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
