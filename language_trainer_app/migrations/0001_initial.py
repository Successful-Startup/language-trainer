import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Case",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Падеж",
                "verbose_name_plural": "Падежи",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Gender",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Род",
                "verbose_name_plural": "Роды",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PartOfSpeech",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Часть речи",
                "verbose_name_plural": "Части речи",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="WordNumber",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Число",
                "verbose_name_plural": "Числа",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Context",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "verbose_name": "Контекст",
                "verbose_name_plural": "Контексты",
                "ordering": ["text"],
            },
        ),
        migrations.CreateModel(
            name="Word",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("base_form", models.CharField(db_index=True, max_length=100)),
                (
                    "gender",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_trainer_app.gender",
                    ),
                ),
                (
                    "part_of_speech",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="language_trainer_app.partofspeech",
                    ),
                ),
            ],
            options={
                "verbose_name": "Слово",
                "verbose_name_plural": "Слова",
                "ordering": ["base_form"],
            },
        ),
        migrations.AddConstraint(
            model_name="word",
            constraint=models.UniqueConstraint(
                fields=["base_form", "part_of_speech", "gender"], name="unique_word"
            ),
        ),
        migrations.CreateModel(
            name="Phrase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("phrase_start", models.CharField(max_length=200)),
                (
                    "valid_words",
                    models.ManyToManyField(to="language_trainer_app.word"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WordForm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("word_form", models.CharField(db_index=True, max_length=100)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="language_trainer_app.case",
                    ),
                ),
                (
                    "gender",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="language_trainer_app.gender",
                    ),
                ),
                (
                    "number",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="language_trainer_app.wordnumber",
                    ),
                ),
                (
                    "word",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forms",
                        to="language_trainer_app.word",
                    ),
                ),
            ],
            options={
                "verbose_name": "Форма слова",
                "verbose_name_plural": "Формы слов",
                "ordering": ["word", "case", "number"],
            },
        ),
        migrations.AddConstraint(
            model_name="wordform",
            constraint=models.UniqueConstraint(
                fields=["word", "case", "gender", "number"], name="unique_word_form"
            ),
        ),
        migrations.CreateModel(
            name="ContextWordFormPair",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "context",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="word_form_pairs",
                        to="language_trainer_app.context",
                    ),
                ),
                # SET_NULL: deleting a WordForm makes the pair adjective-less,
                # not removes the pair entirely.
                (
                    "adjective_form",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="adjective_pairs",
                        to="language_trainer_app.wordform",
                    ),
                ),
                (
                    "noun_form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="noun_pairs",
                        to="language_trainer_app.wordform",
                    ),
                ),
            ],
            options={
                "verbose_name": "Пара контекст-форма",
                "verbose_name_plural": "Пары контекст-форма",
                "ordering": ["context", "noun_form"],
            },
        ),
        # Two partial unique constraints replace the old single constraint on
        # (context, adjective_form, noun_form).  PostgreSQL treats NULL != NULL
        # in standard unique indexes, so without the second constraint a context
        # could accumulate duplicate noun-only pairs.
        migrations.AddConstraint(
            model_name="contextwordformpair",
            constraint=models.UniqueConstraint(
                fields=["context", "adjective_form", "noun_form"],
                condition=models.Q(adjective_form__isnull=False),
                name="unique_context_word_form_pair_with_adjective",
            ),
        ),
        migrations.AddConstraint(
            model_name="contextwordformpair",
            constraint=models.UniqueConstraint(
                fields=["context", "noun_form"],
                condition=models.Q(adjective_form__isnull=True),
                name="unique_context_word_form_pair_without_adjective",
            ),
        ),
    ]
