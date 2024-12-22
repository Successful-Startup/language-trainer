from rest_framework import serializers


class TestParametersSerializer(serializers.Serializer):
    use_adjective = serializers.BooleanField()
    genders = serializers.ListField(child=serializers.IntegerField())
    cases = serializers.ListField(child=serializers.IntegerField())
    numbers = serializers.ListField(child=serializers.IntegerField())
