# Generated by Django 3.0.6 on 2020-06-16 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0015_auto_20200616_2101'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='grade',
            field=models.IntegerField(default=0, null=True, verbose_name='ECF Grade'),
        ),
        migrations.AlterField(
            model_name='player',
            name='ecf',
            field=models.CharField(max_length=7, null=True, verbose_name='ECF Grading Ref'),
        ),
    ]
