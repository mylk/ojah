from django.db import models
from django.utils import timezone
from core.models.newsitem import NewsItem
from django.utils.html import format_html


class Corpus(models.Model):

    class Meta:
        db_table = 'corpus'
        verbose_name = 'corpus'
        verbose_name_plural = 'corpora'

    news_item = models.ForeignKey(NewsItem, null=False, on_delete=models.DO_NOTHING)
    positive = models.BooleanField(default=False, null=False)
    active = models.BooleanField(default=True, null=False)
    added_at = models.DateTimeField(default=timezone.now)

    def get_classification(self):
        return 'pos' if self.positive else 'neg'

    def __str__(self):
        return '{}: {}'.format(self.news_item.title, self.get_classification().upper())

    def news_item_link(self):
        return format_html(
            '<a href="{}">{}</a>',
            self.news_item.url,
            self.news_item.title,
        )

    news_item_link.short_description = 'News Item'
