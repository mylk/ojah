# Generated by Django 3.1.3 on 2020-12-02 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_statistic_pending_classify_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistic',
            name='news_items_not_scored_count',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
