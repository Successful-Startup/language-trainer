from rest_framework import serializers

from language_trainer_app.models.part_of_speech import PartOfSpeech


class PartOfSpeechSerializer(serializers.ModelSerializer):
    """Serializer for parts of speech (части речи)."""

    class Meta:
        model = PartOfSpeech
        fields = ["id", "name", "name_en"]
        read_only_fields = ["id"]
