# Generated by Django 2.2 on 2019-05-08 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_auto_20190425_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semester',
            name='registration_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='semester',
            name='registration_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
