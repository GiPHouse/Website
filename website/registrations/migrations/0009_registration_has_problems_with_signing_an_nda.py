# Generated by Django 4.1.3 on 2023-01-03 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0008_registration_attendance"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="has_problems_with_signing_an_nda",
            field=models.BooleanField(default=False),
        ),
    ]