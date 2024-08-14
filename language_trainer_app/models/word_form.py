from django.db import models


class WordForm(models.Model):
    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    case = models.ForeignKey('Case', on_delete=models.CASCADE)
    gender = models.ForeignKey('Gender', on_delete=models.SET_NULL, null=True)
    number = models.ForeignKey('WordNumber', on_delete=models.CASCADE)
    word_form = models.CharField(max_length=100)

    def __str__(self):
        return self.word_form
