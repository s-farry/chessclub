# Generated by Django 3.1.3 on 2021-02-03 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0027_auto_20210203_1905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='league',
            name='draw_points',
            field=models.IntegerField(choices=[(0, 0), (1, 0.5), (2, 1), (3, 2), (4, 3)], default=0, null=True, verbose_name='Points for draw'),
        ),
        migrations.AlterField(
            model_name='league',
            name='lost_points',
            field=models.IntegerField(choices=[(0, 0), (1, 0.5), (2, 1), (3, 2), (4, 3)], default=0, null=True, verbose_name='Points for loss'),
        ),
        migrations.AlterField(
            model_name='league',
            name='win_points',
            field=models.IntegerField(choices=[(0, 0), (1, 0.5), (2, 1), (3, 2), (4, 3)], default=0, null=True, verbose_name='Points for win'),
        ),
        migrations.AlterField(
            model_name='standings',
            name='form',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
