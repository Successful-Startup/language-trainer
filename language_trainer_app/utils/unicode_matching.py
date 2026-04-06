"""Unicode-aware matching helpers shared across controllers and import code."""

from django.db import connection
from django.db.models import Case, IntegerField, Value, When
from django.db.models.functions import Lower


def _filter_queryset_casefold_exact_python(queryset, field_name, search_term):
    """Fallback path for databases without reliable Unicode case-insensitive exact match."""
    normalized_search_term = search_term.casefold()
    exact_ids = []
    casefold_ids = []

    for object_id, field_value in queryset.values_list("id", field_name):
        if not isinstance(field_value, str):
            continue
        if field_value == search_term:
            exact_ids.append(object_id)
            continue
        if field_value.casefold() == normalized_search_term:
            casefold_ids.append(object_id)

    matching_ids = exact_ids + casefold_ids
    return (
        queryset.filter(id__in=matching_ids)
        .annotate(
            unicode_match_rank=Case(
                When(id__in=exact_ids, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("unicode_match_rank", "-id")
    )


def filter_queryset_casefold_exact(queryset, field_name, search_term):
    """Filter a queryset by exact string match using Python casefold semantics."""
    if connection.vendor != "postgresql":
        return _filter_queryset_casefold_exact_python(queryset, field_name, search_term)

    normalized_search_term = search_term.lower()
    return (
        queryset.annotate(normalized_search_value=Lower(field_name))
        .filter(normalized_search_value=normalized_search_term)
        .annotate(
            unicode_match_rank=Case(
                When(**{field_name: search_term}, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("unicode_match_rank", "-id")
    )
