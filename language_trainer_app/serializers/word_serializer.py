from rest_framework import serializers
from language_trainer_app.models.word import Word


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = "__all__"
