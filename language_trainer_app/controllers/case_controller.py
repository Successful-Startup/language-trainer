from language_trainer_app.models.case import Case
from rest_framework import viewsets
from rest_framework.response import Response

from language_trainer_app.serializers.case_serializer import CaseSerializer
from language_trainer_app.services.case_service import CaseService

class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer

    def list(self, request):
        cases = CaseService.get_all_cases()
        serializer = self.get_serializer(cases, many=True)
        return Response(serializer.data)