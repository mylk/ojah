from django.contrib.syndication.views import Feed
from django.test import TestCase
from rss.models.newsitem import NewsItem
from rss.views.rssfeed import RssFeed


class RssFeedTestCase(TestCase):

    rss_feed = None
    news_item = None

    def setUp(self):
        self.rss_feed = RssFeed()

    def test_item_title_returns_newsitem_title_when_set(self):
        news_item = NewsItem()
        news_item.title = 'foo_title'
        self.assertEquals('foo_title', self.rss_feed.item_title(news_item))

    def test_item_title_returns_empty_string_when_newsitem_title_not_set(self):
        news_item = NewsItem()
        self.assertEquals('', self.rss_feed.item_title(news_item))

    def test_item_description_returns_newsitem_description_when_set(self):
        news_item = NewsItem()
        news_item.description = 'foo_description'
        self.assertEquals('foo_description', self.rss_feed.item_description(news_item))

    def test_item_description_returns_empty_string_when_newsitem_description_not_set(self):
        news_item = NewsItem()
        self.assertEquals('', self.rss_feed.item_description(news_item))

    def test_item_link_returns_newsitem_url_when_set(self):
        news_item = NewsItem()
        news_item.url = 'https://www.google.com'
        self.assertEquals('https://www.google.com', self.rss_feed.item_link(news_item))

    def test_item_link_returns_none_when_newsitem_url_not_set(self):
        news_item = NewsItem()
        self.assertEquals(None, self.rss_feed.item_link(news_item))

    def test_item_pubdate_returns_newsitem_added_at(self):
        news_item = NewsItem()
        self.assertNotEquals(None, self.rss_feed.item_pubdate(news_item))
