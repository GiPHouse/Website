# Generated by Django 2.1.7 on 2019-03-15 10:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('peer_review', '0003_auto_20190315_0942'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionnaire',
            name='active',
        ),
        migrations.AddField(
            model_name='answer',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='answer',
            name='on_time',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
