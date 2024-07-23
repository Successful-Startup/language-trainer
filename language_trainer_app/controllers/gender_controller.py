from language_trainer_app.models.gender import Gender
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from language_trainer_app.serializers.gender_serializer import GenderSerializer
from language_trainer_app.services.gender_service import GenderService

class GenderViewSet(viewsets.ModelViewSet):
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer

    def list(self, request):
        genders = GenderService.get_all_genders()
        serializer = self.get_serializer(genders, many=True)
        return Response(serializer.data)