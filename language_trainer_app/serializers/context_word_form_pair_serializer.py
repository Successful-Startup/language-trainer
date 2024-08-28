from rest_framework import serializers
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair


class ContextWordFormPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextWordFormPair
        fields = "__all__"
