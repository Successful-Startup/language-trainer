from rest_framework import serializers
from LanguageTrainerApp.models.word import Word

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = '__all__'
