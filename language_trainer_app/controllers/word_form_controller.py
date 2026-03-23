from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.word_form import WordForm
from language_trainer_app.serializers.word_form_serializer import WordFormSerializer


class WordFormViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on WordForm model (word declensions)."""

    queryset = WordForm.objects.select_related("word", "case", "gender", "number").all()
    serializer_class = WordFormSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["word_form", "word__base_form"]
