from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from language_trainer_app.models.context import Context
from language_trainer_app.serializers.context_serializer import ContextSerializer


class ContextViewSet(viewsets.ModelViewSet):
    """ViewSet for CRUD operations on Context model (sentence templates)."""

    queryset = Context.objects.all()
    serializer_class = ContextSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
