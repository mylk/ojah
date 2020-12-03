import datetime

from django.db import models
from django.utils import timezone
from core.models.source import Source


class NewsItem(models.Model):

    class Meta:
        db_table = 'news_item'

    title = models.CharField(max_length=300)
    description = models.TextField()
    source = models.ForeignKey(Source, null=True, on_delete=models.DO_NOTHING)
    url = models.CharField(max_length=300)
    score = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    published = models.BooleanField(default=False, null=False)
    added_at = models.DateTimeField(default=timezone.now)

    @staticmethod
    def exists(title, added_at, source):
        news_items_existing = NewsItem.objects.filter(
            title=title,
            added_at__gt=added_at-datetime.timedelta(hours=24),
            source=source
        )
        return len(news_items_existing) > 0

    @staticmethod
    def find_positive(score_threshold, news_items_count):
        return NewsItem.objects.raw('''
            SELECT *
            FROM news_item
            WHERE (
                score > %s
                AND id NOT IN (
                    SELECT news_item_id
                    FROM corpus
                    WHERE positive = 0
                )
                AND published = 1
            ) OR id IN (
                SELECT news_item_id
                FROM corpus
                WHERE positive = 1
            )
            AND published = 1
            ORDER BY added_at DESC
            LIMIT %s
        ''', [score_threshold, news_items_count])

    @staticmethod
    def find_neutral():
        return NewsItem.objects.raw('''
            SELECT *
            FROM news_item
            WHERE published = 0
            AND score = 1
            AND id NOT IN (
                SELECT news_item_id
                FROM corpus
            )
        ''')

    @staticmethod
    def find_negative(score_threshold):
        return NewsItem.objects.raw('''
            SELECT *
            FROM news_item
            WHERE score < %s
            AND id NOT IN (
                SELECT news_item_id
                FROM corpus
                WHERE positive = 1
            )
            AND published = 0
            ORDER BY added_at DESC;
        ''', [score_threshold])

    def __str__(self):
        return self.title
