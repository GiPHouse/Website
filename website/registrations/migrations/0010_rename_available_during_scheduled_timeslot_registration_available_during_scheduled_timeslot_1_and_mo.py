# Generated by Django 4.1.3 on 2023-01-15 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0009_registration_has_problems_with_signing_an_nda"),
    ]

    operations = [
        migrations.RenameField(
            model_name="registration",
            old_name="available_during_scheduled_timeslot",
            new_name="available_during_scheduled_timeslot_1",
        ),
        migrations.RemoveField(
            model_name="registration",
            name="attendance",
        ),
        migrations.AddField(
            model_name="registration",
            name="available_during_scheduled_timeslot_2",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="registration",
            name="available_during_scheduled_timeslot_3",
            field=models.BooleanField(default=True),
        ),
    ]