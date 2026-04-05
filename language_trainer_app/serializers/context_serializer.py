from rest_framework import serializers

from language_trainer_app.models.context import Context


class ContextSerializer(serializers.ModelSerializer):
    """Serializer for context sentences (контексты с пропусками)."""

    class Meta:
        model = Context
        fields = ["id", "text"]
        read_only_fields = ["id"]

    def validate_text(self, value):
        """Validate that context contains exactly one '____' placeholder."""
        count = value.count("____")
        if count == 0:
            raise serializers.ValidationError(
                "Context must contain '____' as the blank placeholder."
            )
        if count > 1:
            raise serializers.ValidationError(
                "Context must contain exactly one '____' placeholder, found more than one."
            )
        return value
