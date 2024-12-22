from rest_framework import serializers


class TestItemSerializer(serializers.Serializer):
    context = serializers.CharField()
    noun_with_adjective = serializers.CharField()
    correct_answer = serializers.CharField()
