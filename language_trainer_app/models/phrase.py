import uuid
from django.db import models

class Phrase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phrase_start = models.CharField(max_length=200)
    valid_words = models.ManyToManyField('Word')

    def __str__(self):
        return self.phrase_start
