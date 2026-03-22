from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_teacher_user(apps, schema_editor):
    """Create the teacher user for authentication."""
    User = apps.get_model("auth", "User")
    if not User.objects.filter(username="Evgenia").exists():
        User.objects.create(
            username="Evgenia",
            password=make_password("Trubnikova"),
            is_staff=True,
            is_active=True,
        )


def remove_teacher_user(apps, schema_editor):
    """Reverse: remove the teacher user."""
    User = apps.get_model("auth", "User")
    User.objects.filter(username="Evgenia").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("language_trainer_app", "0002_seed_reference_data"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_teacher_user, remove_teacher_user),
    ]
