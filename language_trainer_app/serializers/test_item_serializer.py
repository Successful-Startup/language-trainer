from rest_framework import serializers


class TestItemSerializer(serializers.Serializer):
    """Serializer for test items returned by test generator."""

    context = serializers.CharField(help_text="Sentence with placeholder")
    noun_with_adjective = serializers.CharField(help_text="Word(s) in base form")
    correct_answer = serializers.CharField(help_text="Correct declension")
    number_name_en = serializers.CharField(help_text="English name of the word number (e.g. Singular, Plural)")
