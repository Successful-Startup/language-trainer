from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from language_trainer_app.models.word import Word


class WordSerializer(serializers.ModelSerializer):
    """Serializer for words (слова в начальной форме)."""

    class Meta:
        model = Word
        fields = ["id", "base_form", "gender", "part_of_speech", "animacy"]
        read_only_fields = ["id"]
        # DRF skips the model's two partial unique constraints, because their
        # condition is on a foreign key. One check with NULL equal to NULL covers both.
        validators = [
            UniqueTogetherValidator(
                queryset=Word.objects.all(),
                fields=["base_form", "part_of_speech", "gender"],
                nulls_distinct=False,
            )
        ]
        extra_kwargs = {"gender": {"default": None}}
