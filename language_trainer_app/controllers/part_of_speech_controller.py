from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.serializers.part_of_speech_serializer import (
    PartOfSpeechSerializer,
)


class PartOfSpeechViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on PartOfSpeech model."""

    queryset = PartOfSpeech.objects.all()
    serializer_class = PartOfSpeechSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
