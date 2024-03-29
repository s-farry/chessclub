# Generated by Django 2.1.15 on 2023-03-19 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0050_auto_20220924_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='playoffs',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='league',
            name='promotion',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='league',
            name='relegation',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='standings',
            name='position',
            field=models.IntegerField(blank=True, null=True, verbose_name='Position'),
        ),
    ]
