from django.db import models

class Word(models.Model):
    word_nom = models.CharField(max_length=100)
    gender = models.ForeignKey('Gender', on_delete=models.SET_NULL, null=True)
    part_of_speech = models.ForeignKey('PartOfSpeech', on_delete=models.CASCADE)

    def __str__(self):
        return self.word_nom
