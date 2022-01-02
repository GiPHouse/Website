# Generated by Django 3.2 on 2021-12-22 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0007_registration_available_during_scheduled_timeslot'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='attendance',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Attending offline'), (2, 'Only online'), (3, 'Preferably online')], default=1),
        ),
    ]