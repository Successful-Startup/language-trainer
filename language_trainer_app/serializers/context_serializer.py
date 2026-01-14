from rest_framework import serializers

from language_trainer_app.models.context import Context


class ContextSerializer(serializers.ModelSerializer):
    """Serializer for context sentences (контексты с пропусками)."""

    class Meta:
        model = Context
        fields = ["id", "text"]
        read_only_fields = ["id"]

    def validate_text(self, value):
        """Validate that context contains placeholder."""
        if "____" not in value:
            raise serializers.ValidationError(
                "Context must contain '____' placeholder for the word form."
            )
        return value
