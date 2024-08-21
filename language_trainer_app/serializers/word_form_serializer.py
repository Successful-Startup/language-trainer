from rest_framework import serializers
from language_trainer_app.models.word_form import WordForm


class WordFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordForm
        fields = "__all__"
