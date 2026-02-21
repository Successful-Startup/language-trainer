from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.case import Case
from language_trainer_app.serializers.case_serializer import CaseSerializer


class CaseViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Case model (grammatical cases)."""

    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
