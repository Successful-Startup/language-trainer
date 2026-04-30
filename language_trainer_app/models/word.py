from django.db import models


class Word(models.Model):
    class Animacy(models.TextChoices):
        ANIMATE = "Anim", "Одушевлённое"
        INANIMATE = "Inan", "Неодушевлённое"

    base_form = models.CharField(max_length=100, db_index=True)
    gender = models.ForeignKey("Gender", on_delete=models.SET_NULL, null=True)
    part_of_speech = models.ForeignKey("PartOfSpeech", on_delete=models.CASCADE)
    animacy = models.CharField(
        max_length=4,
        choices=Animacy.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["base_form"]
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        constraints = [
            # Standard unique constraint for rows where gender IS NOT NULL.
            models.UniqueConstraint(
                fields=["base_form", "part_of_speech", "gender"],
                condition=models.Q(gender__isnull=False),
                name="unique_word_with_gender",
            ),
            # Separate constraint for rows without a gender (gender IS NULL).
            # PostgreSQL treats NULL != NULL in unique indexes, so without this
            # the same genderless word could be inserted multiple times.
            models.UniqueConstraint(
                fields=["base_form", "part_of_speech"],
                condition=models.Q(gender__isnull=True),
                name="unique_word_without_gender",
            ),
        ]

    def __str__(self):
        return self.base_form
