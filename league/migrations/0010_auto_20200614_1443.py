# Generated by Django 3.0.6 on 2020-06-14 14:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0009_auto_20200614_1436'),
    ]

    operations = [
    	migrations.RenameField('Standings', 'season', 'league')
    ]
