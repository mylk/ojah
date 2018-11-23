from django.test import TestCase
from rss.models.source import Source


class SourceTestCase(TestCase):

    source = None

    def setUp(self):
        self.source = Source()

    def test_crawled_sets_last_crawl_datetime(self):
        self.assertEquals(None, self.source.last_crawl)

        self.source.crawled()
        self.assertNotEquals(None, self.source.last_crawl)

    def test_str_returns_name_when_name_is_set(self):
        self.source.name = 'foo'
        self.assertEquals('foo', str(self.source))

    def test_str_returns_none_when_name_is_not_set(self):
        self.assertEquals('', str(self.source))
