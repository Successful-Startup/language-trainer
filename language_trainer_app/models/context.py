from django.db import models


class Context(models.Model):
    text = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["text"]
        verbose_name = "Контекст"
        verbose_name_plural = "Контексты"

    def __str__(self):
        return self.text
