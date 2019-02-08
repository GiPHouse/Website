# Generated by Django 2.1.5 on 2019-02-09 11:59

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GiphouseProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('github_id', models.IntegerField(unique=True)),
                ('github_username', models.TextField(unique=True)),
                ('snumber', models.IntegerField(null=True, unique=True)),
                ('role', models.CharField(choices=[('se', 'SE Student'), ('sdm', 'SDM Student'), ('director', 'Director'), ('admin', 'Admin')], max_length=8)),
            ],
            options={
                'verbose_name': 'GiPHouse Profile',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('group_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.Group')),
                ('description', models.TextField()),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('semester', models.CharField(choices=[('fall', 'Fall'), ('spring', 'Spring')], max_length=6)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='registrations.Semester'),
        ),
        migrations.AddField(
            model_name='giphouseprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]