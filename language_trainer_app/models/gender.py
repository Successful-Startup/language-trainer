from django.db import models


class Gender(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Род"
        verbose_name_plural = "Роды"

    def __str__(self):
        return self.name
