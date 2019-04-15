from django.db import models
from django.utils import timezone


class Source(models.Model):

    class Meta:
        db_table = 'source'

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    homepage = models.CharField(max_length=100, blank=True, null=True)
    last_crawl = models.DateTimeField(blank=True, null=True)

    def crawled(self):
        self.last_crawl = timezone.now()
        self.save()

    def __str__(self):
        return self.name
