from django.conf import settings
from django.db import models
from django.utils import timezone


class Source(models.Model):

    class Meta:
        db_table = 'source'

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    homepage = models.CharField(max_length=100, blank=True, null=True)
    last_crawl = models.DateTimeField(blank=True, null=True)
    pending = models.BooleanField(blank=False, null=False, default=False)

    def get_minutes_since_last_crawl(self):
        return abs((timezone.now() - self.last_crawl).seconds / 60)

    def crawling(self):
        self.pending = True
        self.save()

    def crawled(self):
        self.last_crawl = timezone.now()
        self.pending = False
        self.save()

    def is_stale(self):
        return self.pending and (
            self.get_minutes_since_last_crawl() >= settings.SOURCE_CRAWL_STALE_MINUTES_THRESHOLD
        )

    def __str__(self):
        return self.name
