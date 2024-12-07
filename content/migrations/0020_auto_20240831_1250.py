# Generated by Django 2.1.15 on 2024-08-31 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0019_auto_20240830_2328'),
    ]

    operations = [
        migrations.CreateModel(
            name='page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField(max_length=1000000)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Plain Page',
                'verbose_name_plural': 'Plain Pages',
            },
        ),
        migrations.RenameModel(
            old_name='htmlobject',
            new_name='snippet',
        ),
    ]
