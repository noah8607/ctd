# Generated by Django 5.0 on 2025-04-02 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediagnosisreport',
            name='treatment_plan',
            field=models.TextField(blank=True),
        ),
    ]
