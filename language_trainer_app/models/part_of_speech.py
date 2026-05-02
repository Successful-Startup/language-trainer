from django.db import models


class PartOfSpeech(models.Model):
    name = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        ordering = ["name"]
        verbose_name = "Часть речи"
        verbose_name_plural = "Части речи"

    def __str__(self):
        return self.name
