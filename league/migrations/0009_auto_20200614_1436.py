# Generated by Django 3.0.6 on 2020-06-14 14:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0008_schedule_lichess'),
    ]

    operations = [
    	migrations.RenameField('Schedule', 'season', 'league')
    ]