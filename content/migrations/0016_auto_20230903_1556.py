# Generated by Django 2.1.15 on 2023-09-03 14:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_auto_20230521_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='dropdownitem',
            name='subitem',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='news',
            name='puzzle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='puzzle', to='content.Puzzle', verbose_name='Puzzle'),
        ),
    ]
