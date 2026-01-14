from django.db import models


class Word(models.Model):
    base_form = models.CharField(max_length=100, db_index=True)
    gender = models.ForeignKey("Gender", on_delete=models.SET_NULL, null=True)
    part_of_speech = models.ForeignKey("PartOfSpeech", on_delete=models.CASCADE)

    class Meta:
        ordering = ["base_form"]
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        constraints = [
            models.UniqueConstraint(
                fields=["base_form", "part_of_speech", "gender"], name="unique_word"
            )
        ]

    def __str__(self):
        return self.base_form
