# Generated by Django 2.2 on 2019-04-25 14:32

from django.db import migrations, models


def move_to_int_choices(apps, schema_editor):
    Semester = apps.get_model('courses', 'semester')
    for semester in Semester.objects.all():
        if semester.seasonold == 'spring':
            semester.season = 0
        if semester.seasonold == 'fall':
            semester.season = 1


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_auto_20190411_2213'),
    ]

    operations = [
        migrations.RenameField(
            model_name='semester',
            old_name='season',
            new_name='seasonold',
        ),
        migrations.AddField(
            model_name='semester',
            name='season',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Spring'), (1, 'Fall')], default=0),
        ),
        migrations.RunPython(
            move_to_int_choices
        ),
        migrations.RemoveField(
            model_name='semester',
            name='seasonold',
        )
    ]
