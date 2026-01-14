from django.db import models
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.context import Context


class ContextWordFormPair(models.Model):
    context = models.ForeignKey(
        Context, on_delete=models.CASCADE, related_name="word_form_pairs"
    )
    adjective_form = models.ForeignKey(
        WordForm,
        on_delete=models.CASCADE,
        related_name="adjective_pairs",
        null=True,
        blank=True,
    )
    noun_form = models.ForeignKey(
        WordForm, on_delete=models.CASCADE, related_name="noun_pairs"
    )

    class Meta:
        ordering = ["context", "noun_form"]
        verbose_name = "Пара контекст-форма"
        verbose_name_plural = "Пары контекст-форма"
        constraints = [
            models.UniqueConstraint(
                fields=["context", "adjective_form", "noun_form"],
                name="unique_context_word_form_pair",
            )
        ]

    def __str__(self):
        adj = self.adjective_form.word_form if self.adjective_form else ""
        return f"{self.context.text}: {adj} {self.noun_form.word_form}".strip()
