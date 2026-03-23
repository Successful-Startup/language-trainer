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
        queryset = super().filter_queryset(queryset)
        search_term = self.request.query_params.get("search", "").strip()
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
