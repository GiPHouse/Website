# Generated by Django 3.0.3 on 2020-04-21 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20200415_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='private',
            field=models.BooleanField(default=True),
        ),
    ]