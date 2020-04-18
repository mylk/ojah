import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from core.models.newsitem import NewsItem
from core.models.source import Source


class NewsItemTestCase(TestCase):

    news_item = None

    def setUp(self):
        self.news_item = NewsItem()

    def test_exists_returns_false_when_newsitem_does_not_exist(self):
        # the source of the news item
        source = Source()
        source.name = 'foo'
        source.save()

        title = 'foo'
        added_at = timezone.now()
        self.news_item.title = title
        self.news_item.added_at = added_at
        self.news_item.source = source
        self.news_item.save()

        # a different source to use while calling exists()
        source = Source()
        source.name = 'bar'
        source.save()

        exists = NewsItem.exists(title, added_at, source)

        self.assertEquals(False, exists)

    def test_exists_returns_true_when_newsitem_exists_and_added_in_threshold(self):
        source = Source()
        source.name = 'foo'
        source.save()

        title = 'foo'
        added_at = timezone.now()
        self.news_item.title = title
        self.news_item.added_at = added_at
        self.news_item.source = source
        self.news_item.save()

        exists = NewsItem.exists(title, added_at, source)

        self.assertEquals(True, exists)

    def test_exists_returns_false_when_newsitem_exists_and_added_out_of_threshold(self):
        source = Source()
        source.name = 'foo'
        source.save()

        title = 'foo'
        added_at = timezone.now()
        self.news_item.title = title
        self.news_item.added_at = added_at-datetime.timedelta(hours=25)
        self.news_item.source = source
        self.news_item.save()

        exists = NewsItem.exists(title, added_at, source)

        self.assertEquals(False, exists)

    def test_find_positive_returns_empty_list_when_no_newsitems_exist(self):
        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )
        self.assertEquals([], list(news_items))

    def test_find_positive_returns_newsitem_when_positive_and_published_newsitem_exists(self):
        self.news_item.score = 1
        self.news_item.published = True
        self.news_item.save()

        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )

        self.assertEquals(1, len(list(news_items)))

    def test_find_positive_returns_empty_list_when_positive_but_no_published_newsitem_exists(self):
        self.news_item.score = 1
        self.news_item.published = False
        self.news_item.save()

        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )

        self.assertEquals([], list(news_items))

    def test_find_positive_returns_empty_list_when_published_but_no_positive_newsitem_exists(self):
        self.news_item.score = 0
        self.news_item.published = True
        self.news_item.save()

        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )

        self.assertEquals([], list(news_items))

    def test_find_positive_returns_empty_list_when_no_positive_and_no_published_newsitem_exists(self):
        self.news_item.score = 0
        self.news_item.published = False
        self.news_item.save()

        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )

        self.assertEquals([], list(news_items))

    def test_find_positive_returns_empty_list_when_unclassified_newsitems_exist(self):
        self.news_item.score = None
        self.news_item.save()

        self.news_item.score = None
        self.news_item.published = True
        self.news_item.save()

        news_items = self.news_item.find_positive(
            settings.SENTIMENT_POLARITY_THRESHOLD,
            settings.RSS_FEED_NEWS_ITEMS_COUNT
        )

        self.assertEquals([], list(news_items))

    def test_str_returns_title_when_title_is_set(self):
        self.news_item.title = 'foo'
        self.assertEquals('foo', str(self.news_item))

    def test_str_returns_none_when_title_is_not_set(self):
        self.assertEquals('', str(self.news_item))
