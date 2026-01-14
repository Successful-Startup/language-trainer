from rest_framework import serializers

from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.serializers.word_serializer import WordSerializer


class WordFormSerializer(serializers.ModelSerializer):
    """Serializer for word forms (склонения слов)."""

    # Nested serializer for reading (GET requests)
    word = WordSerializer(read_only=True)

    # ID field for writing (POST/PUT requests)
    word_id = serializers.PrimaryKeyRelatedField(
        queryset=Word.objects.all(), source="word", write_only=True
    )

    class Meta:
        model = WordForm
        fields = ["id", "word", "word_id", "case", "gender", "number", "word_form"]
        read_only_fields = ["id"]
