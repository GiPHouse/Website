# Generated by Django 2.2.1 on 2019-05-15 15:46

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0007_auto_20190509_1312'),
        ('registrations', '0005_auto_20190515_1101'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together={('user', 'semester')},
        ),
    ]
