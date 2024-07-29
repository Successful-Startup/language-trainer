from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from language_trainer_app.models.word_number import WordNumber
from language_trainer_app.serializers.word_number_serializer import WordNumberSerializer
from language_trainer_app.services.word_number_service import WordNumberService


class WordNumberViewSet(viewsets.ModelViewSet):
    queryset = WordNumber.objects.all()
    serializer_class = WordNumberSerializer

    def list(self, request):
        word_numbers = WordNumberService.get_all_word_numbers()
        serializer = self.get_serializer(word_numbers, many=True)
        return Response(serializer.data)