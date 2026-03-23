from django.db.models import Case, IntegerField, Value, When
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models import Word
from language_trainer_app.serializers import WordSerializer


class WordViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Word model."""

    queryset = Word.objects.select_related("gender", "part_of_speech").all()
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["base_form"]

    def filter_queryset(self, queryset):
        search_term = self.request.query_params.get("search", "").strip()
        match_mode = self.request.query_params.get("match", "").strip().lower()
        part_of_speech_id = self.request.query_params.get("part_of_speech", "").strip()

        if part_of_speech_id:
            queryset = queryset.filter(part_of_speech_id=part_of_speech_id)

        if search_term and match_mode == "exact":
            return queryset.filter(base_form__iexact=search_term)

        queryset = super().filter_queryset(queryset)
        if search_term:
            queryset = queryset.annotate(
                search_rank=Case(
                    When(base_form__iexact=search_term, then=Value(0)),
                    When(base_form__istartswith=search_term, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            ).order_by("search_rank", "base_form")
        return queryset
