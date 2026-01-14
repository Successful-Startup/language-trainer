from rest_framework import viewsets

from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.serializers.context_word_form_pair_serializer import (
    ContextWordFormPairSerializer,
)


class ContextWordFormPairViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on ContextWordFormPair model."""

    queryset = ContextWordFormPair.objects.select_related(
        "context",
        "noun_form",
        "noun_form__word",
        "adjective_form",
        "adjective_form__word",
    ).all()
    serializer_class = ContextWordFormPairSerializer
