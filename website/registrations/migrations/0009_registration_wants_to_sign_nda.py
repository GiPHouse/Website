# Generated by Django 4.1.3 on 2023-01-02 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0008_registration_attendance"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="wants_to_sign_nda",
            field=models.BooleanField(default=False),
        ),
    ]
