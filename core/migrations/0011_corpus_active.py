# Generated by Django 3.1.3 on 2020-11-26 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_statistic'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
