from django.db import migrations


def load_initial_data(apps, schema_editor):
    """Seed reference data: cases, genders, word numbers, parts of speech."""
    Case = apps.get_model("language_trainer_app", "Case")
    Gender = apps.get_model("language_trainer_app", "Gender")
    WordNumber = apps.get_model("language_trainer_app", "WordNumber")
    PartOfSpeech = apps.get_model("language_trainer_app", "PartOfSpeech")

    for name in [
        "Именительный",
        "Родительный",
        "Дательный",
        "Винительный",
        "Творительный",
        "Предложный",
    ]:
        Case.objects.get_or_create(name=name)

    for name in ["Мужской", "Женский", "Средний"]:
        Gender.objects.get_or_create(name=name)

    for name in ["Единственное", "Множественное"]:
        WordNumber.objects.get_or_create(name=name)

    for name in ["Существительное", "Прилагательное"]:
        PartOfSpeech.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("language_trainer_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_initial_data, migrations.RunPython.noop),
    ]
