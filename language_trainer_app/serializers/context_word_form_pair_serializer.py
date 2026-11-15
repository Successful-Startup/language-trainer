from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.serializers.context_serializer import ContextSerializer
from language_trainer_app.serializers.word_form_serializer import WordFormSerializer


class ContextWordFormPairSerializer(serializers.ModelSerializer):
    """Serializer for context-word form pairs."""

    # Nested serializers for reading (GET requests)
    context = ContextSerializer(read_only=True)
    noun_form = WordFormSerializer(read_only=True)
    adjective_form = WordFormSerializer(read_only=True)

    # ID fields for writing (POST/PUT requests)
    context_id = serializers.PrimaryKeyRelatedField(
        queryset=Context.objects.all(), source="context", write_only=True
    )
    noun_form_id = serializers.PrimaryKeyRelatedField(
        queryset=WordForm.objects.all(), source="noun_form", write_only=True
    )
    adjective_form_id = serializers.PrimaryKeyRelatedField(
        queryset=WordForm.objects.all(),
        source="adjective_form",
        write_only=True,
        # The unique-together check treats a field without a default as required.
        default=None,
        allow_null=True,
    )

    class Meta:
        model = ContextWordFormPair
        fields = [
            "id",
            "context",
            "context_id",
            "noun_form",
            "noun_form_id",
            "adjective_form",
            "adjective_form_id",
        ]
        read_only_fields = ["id"]
        # DRF skips the model's two partial unique constraints, because their
        # condition is on a foreign key. One check with NULL equal to NULL covers both.
        validators = [
            UniqueTogetherValidator(
                queryset=ContextWordFormPair.objects.all(),
                fields=["context_id", "adjective_form_id", "noun_form_id"],
                nulls_distinct=False,
            )
        ]
