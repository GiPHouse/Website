# Generated by Django 3.2 on 2021-09-30 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0003_auto_20200525_2158'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnairesubmission',
            name='submitted',
            field=models.BooleanField(default=True),
        ),
    ]