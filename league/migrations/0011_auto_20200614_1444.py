# Generated by Django 3.0.6 on 2020-06-14 14:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0010_auto_20200614_1443'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Season',
            new_name='League',
        ),
        migrations.AlterModelOptions(
            name='league',
            options={'verbose_name': 'League', 'verbose_name_plural': 'Leagues'},
        ),
    ]
