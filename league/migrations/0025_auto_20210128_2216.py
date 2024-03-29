# Generated by Django 3.1.3 on 2021-01-28 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0024_auto_20201230_2105'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='standings',
            options={'ordering': ('-points', '-win', 'lost', 'player__surename'), 'verbose_name': 'Table', 'verbose_name_plural': 'Tables'},
        ),
        migrations.RemoveField(
            model_name='player',
            name='grade',
        ),
        migrations.AddField(
            model_name='league',
            name='format',
            field=models.IntegerField(choices=[(0, 'League'), (1, 'Swiss'), (2, 'Round Robin')], default=1),
        ),
        migrations.AddField(
            model_name='player',
            name='rating',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Rating'),
        ),
        migrations.AddField(
            model_name='standings',
            name='rating',
            field=models.IntegerField(blank=True, null=True, verbose_name='Rating'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='date',
            field=models.DateTimeField(blank=True, choices=[(0, '1/2-1/2'), (1, '1-0'), (2, '0-1'), (3, '-')], null=True, verbose_name='Date'),
        ),
    ]
