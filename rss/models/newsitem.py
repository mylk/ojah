from django.db import models
from django.utils import timezone
from .source import Source


class NewsItem(models.Model):
    class Meta:
        db_table = 'news_item'

    title = models.CharField(max_length=200)
    description = models.TextField()
    source = models.ForeignKey(Source, null=True)
    url = models.URLField(null=True)
    score = models.DecimalField(decimal_places=2, max_digits=10)
    added_at = models.DateTimeField(default=timezone.now)

    @staticmethod
    def exists(title, added_at, source):
        news_items_existing = NewsItem.objects.filter(title=title, added_at=added_at, source=source)
        return len(news_items_existing) > 0

    def __str__(self):
        return self.title
