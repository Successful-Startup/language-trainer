"""Unicode-aware matching helpers shared across controllers and import code."""

from django.db.models import Case, IntegerField, Value, When


def filter_queryset_casefold_exact(queryset, field_name, search_term):
    """Filter a queryset by exact string match using Python casefold semantics."""
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
    return queryset.filter(id__in=matching_ids).annotate(
        unicode_match_rank=Case(
            When(id__in=exact_ids, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("unicode_match_rank", "-id")
