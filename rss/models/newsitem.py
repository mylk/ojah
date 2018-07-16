from django.db import models
from django.utils import timezone
from .source import Source


class NewsItem(models.Model):
    class Meta:
        db_table = 'news_item'

    title = models.CharField(max_length=200)
    description = models.TextField()
    source = models.ForeignKey(Source, null=True, on_delete=models.DO_NOTHING)
    url = models.URLField(null=True)
    score = models.DecimalField(decimal_places=2, max_digits=10)
    added_at = models.DateTimeField(default=timezone.now)

    @staticmethod
    def exists(title, added_at, source):
        news_items_existing = NewsItem.objects.filter(title=title, added_at=added_at, source=source)
        return len(news_items_existing) > 0

    @staticmethod
    def find_by_score(score_threshold, news_items_count):
        return NewsItem.objects.filter(score__gte=score_threshold).order_by('-added_at')[:news_items_count]

    def __str__(self):
        return self.title
