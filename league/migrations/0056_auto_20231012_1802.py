# Generated by Django 2.1.15 on 2023-10-12 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0055_committeemember'),
    ]

    operations = [
        migrations.AddField(
            model_name='standings',
            name='h2h',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Head to Head Record'),
        ),
        migrations.AlterField(
            model_name='league',
            name='standings_order',
            field=models.IntegerField(choices=[(0, 'Points, Wins, Lost'), (1, 'Points, Tiebreak, Wins, Lost, Rating'), (2, 'Points, Score'), (3, 'FIDE Swiss Tiebreak System'), (4, 'Win Percentage'), (5, 'Matches Played'), (6, 'Points, Head-to-Head, Wins, Wins With Black, NBS')], default=0, verbose_name='Standings order'),
        ),
    ]
