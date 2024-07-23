from django.db import models

class Phrase(models.Model):
    phrase_start = models.CharField(max_length=200)
    valid_words = models.ManyToManyField('Word')

    def __str__(self):
        return self.phrase_start
