from rest_framework import serializers
from language_trainer_app.models.context import Context


class ContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = "__all__"
