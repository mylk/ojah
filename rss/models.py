from django.db import models
from django.utils import timezone


class Source(models.Model):
    class Meta:
        db_table = 'source'

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    last_crawl = models.DateTimeField(blank=True, null=True)

    def crawled(self):
        self.last_crawl = timezone.now()
        self.save()

    def __str__(self):
        return self.url


class NewsItem(models.Model):
    class Meta:
        db_table = 'news_item'

    title = models.CharField(max_length=200)
    description = models.TextField()
    source = models.ForeignKey(Source, null=True)
    url = models.URLField(null=True)
    score = models.IntegerField()
    added_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
