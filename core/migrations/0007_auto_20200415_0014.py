# Generated by Django 3.0.5 on 2020-04-15 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_source_pending'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='url',
            field=models.CharField(max_length=300),
        ),
    ]
