from django.contrib.syndication.views import Feed
from django.test import TestCase
from django.utils import timezone
from core.models.newsitem import NewsItem
from rss.views.rssfeed import RssFeed


class RssFeedTestCase(TestCase):

    rss_feed = None
    news_item = None

    def setUp(self):
        self.news_item = NewsItem()
        self.rss_feed = RssFeed()

    def test_items_returns_empty_list_when_newsitem_does_not_exist(self):
        items = self.rss_feed.items()
        self.assertEquals([], list(items))

    def test_items_returns_newsitems_when_positive_newsitem_exists(self):
        self.news_item.score = 1
        self.news_item.published = True
        self.news_item.save()

        items = self.rss_feed.items()
        self.assertEquals(1, len(list(items)))

    def test_items_returns_empty_list_when_no_positive_newsitem_exists(self):
        self.news_item.score = 0
        self.news_item.published = False
        self.news_item.save()

        items = self.rss_feed.items()
        self.assertEquals([], list(items))

    def test_item_title_returns_newsitem_title_when_set(self):
        self.news_item.title = 'foo_title'
        self.assertEquals('foo_title', self.rss_feed.item_title(self.news_item))

    def test_item_title_returns_empty_string_when_newsitem_title_not_set(self):
        self.assertEquals('', self.rss_feed.item_title(self.news_item))

    def test_item_description_returns_newsitem_description_when_set(self):
        self.news_item.description = 'foo_description'
        self.assertEquals('foo_description', self.rss_feed.item_description(self.news_item))

    def test_item_description_returns_empty_string_when_newsitem_description_not_set(self):
        self.assertEquals('', self.rss_feed.item_description(self.news_item))

    def test_item_link_returns_newsitem_url_when_set(self):
        self.news_item.url = 'https://www.google.com'
        self.assertEquals('https://www.google.com', self.rss_feed.item_link(self.news_item))

    def test_item_link_returns_none_when_newsitem_url_not_set(self):
        self.assertEquals(None, self.rss_feed.item_link(self.news_item))

    def test_item_pubdate_returns_none_when_newsitem_added_at_not_set(self):
        self.assertNotEquals(None, self.rss_feed.item_pubdate(self.news_item))

    def test_item_pubdate_returns_newsitem_added_at_datetime_when_set(self):
        self.news_item.url = timezone.now()
        self.assertNotEquals(None, self.rss_feed.item_pubdate(self.news_item))
