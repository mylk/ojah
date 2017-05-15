from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from ..models.newsitem import NewsItem


class RssFeed(Feed):
    feed_type = Rss201rev2Feed

    title = settings.RSS_FEED_TITLE
    description = settings.RSS_FEED_DESCRIPTION
    link = reverse_lazy('rss:feed')

    def items(self):
        return NewsItem.objects.filter(score__gte=0.5).order_by('-added_at')[:50]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.added_at
