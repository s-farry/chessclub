# Generated by Django 2.1.15 on 2022-04-15 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0038_auto_20220307_2233'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='standings',
            options={'ordering': ('-points', '-win', 'lost', 'matches', '-rating', 'player__surename'), 'verbose_name': 'Table', 'verbose_name_plural': 'Tables'},
        ),
        migrations.AlterField(
            model_name='player',
            name='rating',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='result',
            field=models.IntegerField(choices=[(0, '1/2-1/2'), (1, '1-0'), (2, '0-1'), (3, '-'), (4, '+--'), (5, '--+')], default=3, verbose_name='result'),
        ),
    ]
