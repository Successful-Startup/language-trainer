from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.serializers.part_of_speech_serializer import (
    PartOfSpeechSerializer,
)
from language_trainer_app.services.part_of_speech_service import PartOfSpeechService


class PartOfSpeechViewSet(viewsets.ModelViewSet):
    queryset = PartOfSpeech.objects.all()
    serializer_class = PartOfSpeechSerializer

    def list(self, request):
        genders = PartOfSpeechService.get_all_parts_of_speech()
        serializer = self.get_serializer(genders, many=True)
        return Response(serializer.data)
