from rest_framework import serializers

from language_trainer_app.models.case import Case
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.word_number import WordNumber


class TestParametersSerializer(serializers.Serializer):
    """Serializer for test generation parameters."""

    use_adjective = serializers.BooleanField()
    genders = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of gender IDs to include in test",
    )
    cases = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of case IDs to include in test",
    )
    numbers = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of number IDs to include in test",
    )

    def validate_genders(self, value):
        """Validate that all gender IDs exist."""
        existing_ids = set(
            Gender.objects.filter(id__in=value).values_list("id", flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid gender IDs: {list(invalid_ids)}"
            )
        return value

    def validate_cases(self, value):
        """Validate that all case IDs exist."""
        existing_ids = set(
            Case.objects.filter(id__in=value).values_list("id", flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"Invalid case IDs: {list(invalid_ids)}")
        return value

    def validate_numbers(self, value):
        """Validate that all number IDs exist."""
        existing_ids = set(
            WordNumber.objects.filter(id__in=value).values_list("id", flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid number IDs: {list(invalid_ids)}"
            )
        return value
