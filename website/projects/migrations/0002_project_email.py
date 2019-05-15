# Generated by Django 2.2 on 2019-05-08 13:23

from django.db import migrations, models
from django.utils.text import slugify


def create_emails(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')

    CHOICES = (
        'spring',
        'fall',
    )

    for project in Project.objects.all():
        project.email = (f'{project.semester.year}'
                         f'{CHOICES[project.semester.season]}-'
                         f'{slugify(project.name)}'
                         f'@giphouse.nl')
        project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='email',
            field=models.EmailField(max_length=254, null=True),
            preserve_default=False,
        ),
        migrations.RunPython(code=create_emails),
        migrations.AlterField(
            model_name='project',
            name='email',
            field=models.EmailField(max_length=254, null=False, blank=True),
        )
    ]
