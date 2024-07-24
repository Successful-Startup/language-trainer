from rest_framework import serializers
from language_trainer_app.models.case import Case

class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = '__all__'
