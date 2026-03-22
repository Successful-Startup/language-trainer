"""Tests for csv_import_utils helper functions."""

from unittest.mock import MagicMock

import pytest

from language_trainer_app.models.gender import Gender
from language_trainer_app.utils.csv_import_utils import (
    MAX_ERRORS,
    find_reference_or_error,
    format_import_response,
)


class TestFindReferenceOrError:
    def test_returns_none_for_falsy_value(self):
        model = MagicMock()
        result = find_reference_or_error(model, "name", "", "Prefix")
        assert result is None
        model.objects.filter.assert_not_called()

    def test_returns_none_for_none_value(self):
        model = MagicMock()
        result = find_reference_or_error(model, "name", None, "Prefix")
        assert result is None

    def test_returns_object_when_found(self, db):
        gender = Gender.objects.create(name="мужской")
        result = find_reference_or_error(Gender, "name", "мужской", "Invalid gender")
        assert result == gender

    def test_case_insensitive_lookup(self, db):
        gender = Gender.objects.create(name="мужской")
        result = find_reference_or_error(Gender, "name", "МУЖСКОЙ", "Invalid gender")
        assert result == gender

    def test_raises_value_error_when_not_found(self, db):
        with pytest.raises(ValueError, match="Invalid gender 'несуществующий'"):
            find_reference_or_error(Gender, "name", "несуществующий", "Invalid gender")


class TestFormatImportResponse:
    def test_success_when_no_errors(self):
        result = format_import_response(10, 8, 2, [])
        assert result["success"] is True
        assert result["total_rows"] == 10
        assert result["created"] == 8
        assert result["skipped"] == 2
        assert result["errors"] == 0
        assert result["error_details"] == []

    def test_failure_when_errors_present(self):
        errors = ["Row 2: bad data", "Row 3: missing field"]
        result = format_import_response(5, 3, 0, errors)
        assert result["success"] is False
        assert result["errors"] == 2
        assert result["error_details"] == errors

    def test_truncates_errors_beyond_max(self):
        errors = [f"Row {i}: error" for i in range(MAX_ERRORS + 5)]
        result = format_import_response(MAX_ERRORS + 5, 0, 0, errors)
        # error_details should be MAX_ERRORS items + 1 sentinel
        assert len(result["error_details"]) == MAX_ERRORS + 1
        assert "more validation errors" in result["error_details"][-1]

    def test_errors_count_reflects_full_list(self):
        errors = [f"Row {i}: error" for i in range(MAX_ERRORS + 5)]
        result = format_import_response(MAX_ERRORS + 5, 0, 0, errors)
        assert result["errors"] == MAX_ERRORS + 5
