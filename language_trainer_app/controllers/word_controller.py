from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models import Word
from language_trainer_app.serializers import WordSerializer


class WordViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Word model."""

    queryset = Word.objects.select_related("gender", "part_of_speech").all()
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
