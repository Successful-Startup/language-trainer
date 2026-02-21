from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.word_number import WordNumber
from language_trainer_app.serializers.word_number_serializer import WordNumberSerializer


class WordNumberViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on WordNumber model (singular/plural)."""

    queryset = WordNumber.objects.all()
    serializer_class = WordNumberSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
