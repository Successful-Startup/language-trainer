from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_teacher_user(apps, schema_editor):
    """Create teacher user for authentication."""
    User = apps.get_model("auth", "User")

    # Create teacher user if not exists
    if not User.objects.filter(username="Evgenia").exists():
        User.objects.create(
            username="Evgenia",
            password=make_password("Trubnikova"),
            is_staff=True,  # Allow access to admin panel
            is_active=True,
        )


def remove_teacher_user(apps, schema_editor):
    """Remove teacher user (reverse migration)."""
    User = apps.get_model("auth", "User")
    User.objects.filter(username="Evgenia").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("language_trainer_app", "0002_auto_20240722_2132"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_teacher_user, remove_teacher_user),
    ]
