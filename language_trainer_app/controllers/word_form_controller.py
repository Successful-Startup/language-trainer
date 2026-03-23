from django.db.models import Case, IntegerField, Value, When
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

    def filter_queryset(self, queryset):
        search_term = self.request.query_params.get("search", "").strip()
        match_mode = self.request.query_params.get("match", "").strip().lower()
        search_field = self.request.query_params.get("search_field", "").strip().lower()
        word_part_of_speech_id = self.request.query_params.get(
            "word_part_of_speech", ""
        ).strip()

        if word_part_of_speech_id:
            queryset = queryset.filter(word__part_of_speech_id=word_part_of_speech_id)

        if search_term and match_mode == "exact":
            if search_field == "base_form":
                return queryset.filter(word__base_form__iexact=search_term)
            return queryset.filter(word_form__iexact=search_term)

        queryset = super().filter_queryset(queryset)
        if search_term:
            queryset = queryset.annotate(
                search_rank=Case(
                    When(word_form__iexact=search_term, then=Value(0)),
                    When(word_form__istartswith=search_term, then=Value(1)),
                    When(word__base_form__iexact=search_term, then=Value(2)),
                    When(word__base_form__istartswith=search_term, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            ).order_by("search_rank", "word_form")
        return queryset
