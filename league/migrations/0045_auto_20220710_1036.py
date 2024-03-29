# Generated by Django 2.1.15 on 2022-07-10 09:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0044_auto_20220710_1033'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='captain',
        ),
        migrations.RemoveField(
            model_name='team',
            name='listed_players',
        ),
        migrations.RemoveField(
            model_name='team',
            name='players',
        ),
        migrations.AddField(
            model_name='teamplayer',
            name='player',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='league.Player', verbose_name='Team Player'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='teamplayer',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='league.Team', verbose_name='Team'),
        ),
    ]
