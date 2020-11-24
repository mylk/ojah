from django.db import models
from django.utils import timezone


class Statistic(models.Model):

    class Meta:
        db_table = 'statistics'

    accuracy_total = models.SmallIntegerField(null=True)
    news_items_count = models.PositiveIntegerField(null=True)
    corpora_count = models.IntegerField(null=True)
    sources_count = models.SmallIntegerField(null=True)
    created_at = models.DateTimeField(default=timezone.now)
