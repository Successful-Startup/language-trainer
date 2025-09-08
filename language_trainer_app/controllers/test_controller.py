# test_controller.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from language_trainer_app.models.test_parameters import TestParameters
from language_trainer_app.serializers.test_item_serializer import TestItemSerializer
from language_trainer_app.serializers.test_parameters_serializer import (
    TestParametersSerializer,
)
from ..services.context_word_form_pair_service import (
    ContextWordFormPairService,
)
from language_trainer_app.services.test_generator_service import TestGeneratorService


class TestViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_service = TestGeneratorService(ContextWordFormPairService())

    @action(detail=False, methods=["post"])
    def generate(self, request):
        serializer = TestParametersSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        test_params = TestParameters(
            use_adjective=validated_data["use_adjective"],
            genders=validated_data["genders"],
            cases=validated_data["cases"],
            numbers=validated_data["numbers"],
        )

        # Generate up to 10 random test items
        test_items = self.test_service.generate_tests(test_params, count=10)
        # test_items should be a list of TestItem objects
        test_item_serializer = TestItemSerializer(test_items, many=True)
        return Response(test_item_serializer.data)
