"""
Utility functions for CSV import.
Includes file validation, reference-object lookup, and response formatting.
"""

from rest_framework.response import Response
from rest_framework import status

from language_trainer_app.utils.unicode_matching import filter_queryset_casefold_exact

MAX_ERRORS = 20


def validate_uploaded_file(request):
    """
    Validate the uploaded CSV file (presence, extension, size).

    Returns:
        Response with error details, or None if validation passed.
    """
    if "file" not in request.FILES:
        return Response(
            {"success": False, "error": "No file provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES["file"]

    if not file.name.endswith(".csv"):
        return Response(
            {"success": False, "error": "File must be .csv format"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.size > 10 * 1024 * 1024:
        return Response(
            {"success": False, "error": "File too large (max 10MB)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def find_reference_or_error(model, name_field, value, error_prefix):
    """
    Look up a reference object by name (case-insensitive) using a DB-level query.

    Args:
        model: Django model to search.
        name_field: field name to filter on (typically 'name').
        value: the value to search for.
        error_prefix: prefix for the error message.

    Returns:
        Model instance, or None if value is falsy.

    Raises:
        ValueError: if no matching object is found.
    """
    if not value:
        return None

    obj = filter_queryset_casefold_exact(model.objects.all(), name_field, value).first()
    if obj is None:
        raise ValueError(f"{error_prefix} '{value}'")
    return obj


def format_import_response(total_rows, created_count, skipped_count, errors):
    """
    Build the import response payload.

    Args:
        total_rows: number of data rows processed.
        created_count: number of records created.
        skipped_count: number of records that already existed (skipped).
        errors: list of error strings (may be longer than MAX_ERRORS).

    Returns:
        dict suitable for a DRF Response.
    """
    error_count = len(errors)
    limited_errors = errors[:MAX_ERRORS]
    if error_count > MAX_ERRORS:
        limited_errors.append(
            f"...and {error_count - MAX_ERRORS} more validation errors"
        )

    return {
        "success": error_count == 0,
        "total_rows": total_rows,
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count,
        "error_details": limited_errors,
    }


def validate_csv_headers(csv_reader, required_headers, optional_headers=None):
    """
    Validate that all required headers are present in the CSV.

    Args:
        csv_reader: csv.DictReader instance.
        required_headers: list of mandatory column names.
        optional_headers: list of optional column names (unused, kept for API compat).

    Returns:
        Response with error details, or None if validation passed.
    """
    if not csv_reader.fieldnames:
        return Response(
            {"success": False, "error": "CSV file has no headers"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    missing = [h for h in required_headers if h not in csv_reader.fieldnames]
    if missing:
        return Response(
            {"success": False, "error": f"Missing required headers: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def safe_get_row_value(row, field_name, required=True):
    """
    Safely extract a stripped value from a CSV row dict.

    Args:
        row: dict representing a CSV row.
        field_name: column name.
        required: if True, raises ValueError when the field is empty.

    Returns:
        str value (never empty when required=True), or None when the field is
        absent/empty and required=False.

    Raises:
        ValueError: if a required field is empty.
    """
    value: str = row.get(field_name, "").strip()

    if not value:
        if required:
            raise ValueError(f"{field_name} is required")
        return None

    return value
