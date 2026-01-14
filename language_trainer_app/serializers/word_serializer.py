from rest_framework import serializers

from language_trainer_app.models.word import Word


class WordSerializer(serializers.ModelSerializer):
    """Serializer for words (слова в начальной форме)."""

    class Meta:
        model = Word
        fields = ["id", "base_form", "gender", "part_of_speech"]
        read_only_fields = ["id"]
