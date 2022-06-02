# Generated by Django 2.1.15 on 2022-04-29 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0040_auto_20220427_0912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='league',
            name='standings_order',
            field=models.IntegerField(choices=[(0, 'Points, Wins, Lost'), (1, 'Points, Tiebreak, Wins, Lost, Rating'), (2, 'Points, Score'), (3, 'FIDE Swiss Tiebreak System'), (4, 'Win Percentage')], default=0, verbose_name='Standings order'),
        ),
    ]