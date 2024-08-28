from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.serializers.context_word_form_pair_serializer import ContextWordFormPairSerializer
from language_trainer_app.services.context_word_form_pair_service import ContextWordFormPairService


class ContextWordFormPairViewSet(viewsets.ModelViewSet):
    queryset = ContextWordFormPair.objects.all()
    serializer_class = ContextWordFormPairSerializer

    # GET /context_word_form_pairs
    def list(self, request):
        queryset = ContextWordFormPairService.get_all_context_word_form_pairs()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # GET /context_word_form_pairs/{context_word_form_pair_id}
    def retrieve(self, request, pk=None):
        try:
            instance = ContextWordFormPairService.get_context_word_form_pair_by_id(pk)
        except ContextWordFormPair.DoesNotExist:
            raise NotFound(detail="Word not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # POST /context_word_form_pairs
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ContextWordFormPairService.create_context_word_form_pair(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /context_word_form_pairs/{context_word_form_pair_id}
    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        ContextWordFormPairService.update_context_word_form_pair(instance.id, serializer.validated_data)
        return Response(serializer.data)

    # DELETE /context_word_form_pairs/{context_word_form_pair_id}
    def destroy(self, request):
        instance = self.get_object()
        ContextWordFormPairService.delete_context_word_form_pair(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

