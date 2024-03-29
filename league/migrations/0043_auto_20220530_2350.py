# Generated by Django 2.1.15 on 2022-05-30 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0042_auto_20220429_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='listed_players',
            field=models.ManyToManyField(blank=True, related_name='listed_team_players', to='league.Player', verbose_name='Listed Players'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='league',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='league.League', verbose_name='League'),
        ),
    ]
