# Generated by Django 2.2.6 on 2019-11-07 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='comments',
            field=models.TextField(blank=True, help_text='This is for private comments that are only available here.', null=True),
        ),
    ]
