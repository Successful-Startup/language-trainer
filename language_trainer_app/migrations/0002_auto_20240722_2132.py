# Generated by Django 5.0.7 on 2024-07-22 21:32

from django.db import migrations

def load_initial_data(apps, schema_editor):
    Case = apps.get_model('language_trainer_app', 'Case')
    Gender = apps.get_model('language_trainer_app', 'Gender')
    Number = apps.get_model('language_trainer_app', 'WordNumber')
    PartOfSpeech = apps.get_model('language_trainer_app', 'PartOfSpeech')
    
    cases = ['Именительный', 'Родительный', 'Дательный', 'Винительный', 'Творительный', 'Предложный']
    genders = ['Мужской', 'Женский', 'Средний']
    numbers = ['Единственное', 'Множественное']
    parts_of_speech = ['Существительное', 'Прилагательное']

    for case in cases:
        Case.objects.get_or_create(name=case)
    
    for gender in genders:
        Gender.objects.get_or_create(name=gender)
    
    for number in numbers:
        Number.objects.get_or_create(name=number)
    
    for part in parts_of_speech:
        PartOfSpeech.objects.get_or_create(name=part)

class Migration(migrations.Migration):

    dependencies = [
        ('language_trainer_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
