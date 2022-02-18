# Generated by Django 2.1.15 on 2022-01-17 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0034_standings_performance'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='ecf_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='event_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='results_officer',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='results_officer_address',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='treasurer',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='season',
            name='treasurer_address',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]