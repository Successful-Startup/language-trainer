from rest_framework import serializers

from language_trainer_app.models.case import Case


class CaseSerializer(serializers.ModelSerializer):
    """Serializer for grammatical cases (падежи)."""

    class Meta:
        model = Case
        fields = ["id", "name"]
        read_only_fields = ["id"]
