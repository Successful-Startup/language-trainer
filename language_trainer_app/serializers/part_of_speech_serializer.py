from rest_framework import serializers
from language_trainer_app.models.part_of_speech import PartOfSpeech


class PartOfSpeechSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartOfSpeech
        fields = "__all__"
