from django.db import models

class AdjectiveForm(models.Model):
    adjective = models.ForeignKey('Adjective', on_delete=models.CASCADE)
    case = models.ForeignKey('Case', on_delete=models.CASCADE)
    gender = models.ForeignKey('Gender', on_delete=models.SET_NULL, null=True)
    number = models.ForeignKey('WordNumber', on_delete=models.CASCADE)
    adjective_form = models.CharField(max_length=100)

    def __str__(self):
        return self.adjective_form
