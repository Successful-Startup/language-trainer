# language_trainer_app/controllers/word_controler.py
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from language_trainer_app.models import Word
from language_trainer_app.serializers import WordSerializer
from language_trainer_app.services import WordService


class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer

    # GET /words
    def list(self, request):
        queryset = WordService.get_all_words()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # GET /words/{word_id}
    def retrieve(self, request, pk=None):
        try:
            instance = WordService.get_word_by_id(pk)
        except Word.DoesNotExist:
            raise NotFound(detail="Word not found.", code=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # POST /words
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        WordService.create_word(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /words/{word_id}
    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        WordService.update_word(instance.id, serializer.validated_data)
        return Response(serializer.data)

    # DELETE /words/{word_id}
    def destroy(self, request):
        instance = self.get_object()
        WordService.delete_word(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
