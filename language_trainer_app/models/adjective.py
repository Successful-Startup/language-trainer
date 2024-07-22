import uuid
from django.db import models

class Adjective(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adjective_nom = models.CharField(max_length=100)
    part_of_speech = models.ForeignKey('PartOfSpeech', on_delete=models.CASCADE)

    def __str__(self):
        return self.adjective_nom
