from rest_framework import serializers

from language_trainer_app.models.gender import Gender


class GenderSerializer(serializers.ModelSerializer):
    """Serializer for grammatical genders (роды)."""

    class Meta:
        model = Gender
        fields = ["id", "name"]
        read_only_fields = ["id"]
