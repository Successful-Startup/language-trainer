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
            # Standard unique constraint for rows where gender IS NOT NULL.
            models.UniqueConstraint(
                fields=["word", "case", "gender", "number"],
                condition=models.Q(gender__isnull=False),
                name="unique_word_form_with_gender",
            ),
            # Separate constraint for rows without a form gender (gender IS NULL).
            # PostgreSQL treats NULL != NULL in unique indexes, so without this the
            # same genderless word form could be inserted multiple times.
            models.UniqueConstraint(
                fields=["word", "case", "number"],
                condition=models.Q(gender__isnull=True),
                name="unique_word_form_without_gender",
            ),
        ]

    def __str__(self):
        return self.word_form
