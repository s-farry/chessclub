# Generated by Django 3.0.6 on 2020-05-16 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0007_auto_20200516_1048'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='lichess',
            field=models.CharField(max_length=200, null=True, verbose_name='Lichess ID'),
        ),
    ]
