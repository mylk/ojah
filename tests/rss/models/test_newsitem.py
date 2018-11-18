from django.test import TestCase
from rss.models.newsitem import NewsItem


class NewsItemTestCase(TestCase):

    news_item = None

    def setUp(self):
        self.news_item = NewsItem()

    def test_str_returns_title_when_title_is_set(self):
        self.news_item.title = 'foo'
        self.assertEquals('foo', str(self.news_item))

    def test_str_returns_none_when_title_is_not_set(self):
        self.assertEquals('', str(self.news_item))
