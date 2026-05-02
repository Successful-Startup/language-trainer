from django.db import migrations


CASE_TRANSLATIONS = {
    "Именительный": "Nominative",
    "Родительный": "Genitive",
    "Дательный": "Dative",
    "Винительный": "Accusative",
    "Творительный": "Instrumental",
    "Предложный": "Prepositional",
}

GENDER_TRANSLATIONS = {
    "Мужской": "Masculine",
    "Женский": "Feminine",
    "Средний": "Neuter",
}

WORD_NUMBER_TRANSLATIONS = {
    "Единственное": "Singular",
    "Множественное": "Plural",
}

PART_OF_SPEECH_TRANSLATIONS = {
    "Существительное": "Noun",
    "Прилагательное": "Adjective",
}


def populate_english_names(apps, schema_editor):
    Case = apps.get_model("language_trainer_app", "Case")
    Gender = apps.get_model("language_trainer_app", "Gender")
    WordNumber = apps.get_model("language_trainer_app", "WordNumber")
    PartOfSpeech = apps.get_model("language_trainer_app", "PartOfSpeech")

    for model, translations in [
        (Case, CASE_TRANSLATIONS),
        (Gender, GENDER_TRANSLATIONS),
        (WordNumber, WORD_NUMBER_TRANSLATIONS),
        (PartOfSpeech, PART_OF_SPEECH_TRANSLATIONS),
    ]:
        for russian_name, english_name in translations.items():
            model.objects.filter(name=russian_name).update(name_en=english_name)


def clear_english_names(apps, schema_editor):
    Case = apps.get_model("language_trainer_app", "Case")
    Gender = apps.get_model("language_trainer_app", "Gender")
    WordNumber = apps.get_model("language_trainer_app", "WordNumber")
    PartOfSpeech = apps.get_model("language_trainer_app", "PartOfSpeech")

    for model in [Case, Gender, WordNumber, PartOfSpeech]:
        model.objects.all().update(name_en="")


class Migration(migrations.Migration):

    dependencies = [
        ("language_trainer_app", "0008_add_name_en_to_reference_models"),
    ]

    operations = [
        migrations.RunPython(populate_english_names, clear_english_names),
    ]
