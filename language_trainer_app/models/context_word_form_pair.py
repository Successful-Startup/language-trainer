from django.db import models
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.context import Context


class ContextWordFormPair(models.Model):
    context = models.ForeignKey(Context, on_delete=models.CASCADE)
    adjective_form = models.ForeignKey(WordForm, on_delete=models.CASCADE, related_name='adjective_form', null=True,
                                       blank=True)
    noun_form = models.ForeignKey(WordForm, on_delete=models.CASCADE, related_name='noun_form')

    # def __str__(self):
    #     return self.context, self.adjective_form, self.noun_form
