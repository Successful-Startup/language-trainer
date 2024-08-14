from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.serializers.word_form_serializer import WordFormSerializer
from language_trainer_app.services.word_form_service import WordFormService


class WordFormViewSet(viewsets.ModelViewSet):
    queryset = WordForm.objects.all()
    serializer_class = WordFormSerializer

    # GET /word_forms
    def list(self, request):
        queryset = WordFormService.get_all_word_forms()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # GET /word_forms/{word_form_id}
    def retrieve(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # POST /word_forms
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        WordFormService.create_word_form(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /word_forms/{word_form_id}
    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        WordFormService.update_word_form(instance.id, serializer.validated_data)
        return Response(serializer.data)

    # DELETE /word_forms/{word_form_id}
    def destroy(self, request):
        instance = self.get_object()
        WordFormService.delete_word_form(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

# TODO: add *args and **kwargs to methods?
# Autocomplete suggests def create(self, request, *args, **kwargs) for example.
# Also methods get underlined in IDE because of discrepancy
