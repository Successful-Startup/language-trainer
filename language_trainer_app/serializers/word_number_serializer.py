from rest_framework import serializers
from language_trainer_app.models.word_number import WordNumber


class WordNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordNumber
        fields = "__all__"
