# Generated by Django 2.1.15 on 2023-04-09 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0013_htmlobject'),
    ]

    operations = [
        migrations.AddField(
            model_name='htmlobject',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
