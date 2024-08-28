from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from language_trainer_app.models.context import Context
from language_trainer_app.serializers.context_serializer import ContextSerializer
from language_trainer_app.services.context_service import ContextService


class ContextViewSet(viewsets.ModelViewSet):
    queryset = Context.objects.all()
    serializer_class = ContextSerializer

    # GET /contexts
    def list(self, request):
        queryset = ContextService.get_all_contexts()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # GET /contexts/{context_id}
    def retrieve(self, request, pk=None):
        try:
            instance = ContextService.get_context_by_id(pk)
        except Context.DoesNotExist:
            raise NotFound(detail="Context not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # POST /contexts
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ContextService.create_context(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /contexts/{context_id}
    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        ContextService.update_context(instance.id, serializer.validated_data)
        return Response(serializer.data)

    # DELETE /contexts/{context_id}
    def destroy(self, request):
        instance = self.get_object()
        ContextService.delete_context(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
