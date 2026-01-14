from rest_framework import serializers

from language_trainer_app.models.word_number import WordNumber


class WordNumberSerializer(serializers.ModelSerializer):
    """Serializer for grammatical numbers (единственное/множественное)."""

    class Meta:
        model = WordNumber
        fields = ["id", "name"]
        read_only_fields = ["id"]
