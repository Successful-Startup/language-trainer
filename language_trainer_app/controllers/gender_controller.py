from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.gender import Gender
from language_trainer_app.serializers.gender_serializer import GenderSerializer


class GenderViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Gender model (grammatical genders)."""

    queryset = Gender.objects.all()
    serializer_class = GenderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
