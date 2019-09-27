# Generated by Django 2.2.5 on 2019-09-27 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('questionnaires', '0001_initial'),
        ('registrations', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnairesubmission',
            name='participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registrations.Student'),
        ),
        migrations.AddField(
            model_name='questionnairesubmission',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaires.Questionnaire'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.Semester'),
        ),
        migrations.AddField(
            model_name='question',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaires.Questionnaire'),
        ),
        migrations.AddField(
            model_name='qualityanswerdata',
            name='answer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='qualityanswerdata', to='questionnaires.Answer'),
        ),
        migrations.AddField(
            model_name='openanswerdata',
            name='answer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='questionnaires.Answer'),
        ),
        migrations.AddField(
            model_name='answer',
            name='peer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answer_about_user', to='registrations.Student'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaires.Question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='questionnaires.QuestionnaireSubmission'),
        ),
        migrations.AddField(
            model_name='agreementanswerdata',
            name='answer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agreementanswerdata', to='questionnaires.Answer'),
        ),
    ]
