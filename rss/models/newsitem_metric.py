from .newsitem import NewsItem


class NewsItemMetric(NewsItem):

    class Meta:
        proxy = True
        verbose_name = 'news item metric'
        verbose_name_plural = 'news item metrics'
