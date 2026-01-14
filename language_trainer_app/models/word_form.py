from django.db import models


class WordForm(models.Model):
    word = models.ForeignKey("Word", on_delete=models.CASCADE, related_name="forms")
    case = models.ForeignKey("Case", on_delete=models.CASCADE)
    gender = models.ForeignKey("Gender", on_delete=models.SET_NULL, null=True)
    number = models.ForeignKey("WordNumber", on_delete=models.CASCADE)
    word_form = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["word", "case", "number"]
        verbose_name = "Форма слова"
        verbose_name_plural = "Формы слов"
        constraints = [
            models.UniqueConstraint(
                fields=["word", "case", "gender", "number"], name="unique_word_form"
            )
        ]

    def __str__(self):
        return self.word_form
