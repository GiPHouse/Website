# Generated by Django 3.2.10 on 2022-02-01 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room_reservation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='special_availability',
            field=models.JSONField(blank=True, help_text='If filled in, the room will only accept reservations during the specified timeslots. Enter valid JSON in the following format: [{"from":"2022-01-31|08:00","until":"2022-02-01|18:00"},{"from":"2022-02-02|15:30","until":"2022-02-02|18:00"}].', null=True),
        ),
    ]
