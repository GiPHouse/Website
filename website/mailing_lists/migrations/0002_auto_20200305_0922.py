# Generated by Django 3.0.3 on 2020-03-05 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailing_lists', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailinglist',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
