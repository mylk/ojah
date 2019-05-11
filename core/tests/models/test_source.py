from datetime import datetime
import mock
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models.source import Source


class SourceTestCase(TestCase):

    source = None

    def setUp(self):
        self.source = Source()

    @patch('django.utils.timezone.now')
    def test_get_minutes_since_last_crawl(self, timezone_mock):
        # mock django.utils.timezone.now
        timezone_mock.return_value = datetime.strptime('2018-05-11 01:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')
        # souce was last crawled 30 minutes before
        self.source.last_crawl = datetime.strptime('2018-05-11 00:30:00+00:00', '%Y-%m-%d %H:%M:%S%z')

        self.assertEquals(30, self.source.get_minutes_since_last_crawl())

    def test_crawling_sets_pending_to_true(self):
        self.assertEquals(False, self.source.pending)

        self.source.crawling()
        self.assertEquals(True, self.source.pending)

    def test_crawled_sets_pending_and_last_crawl_datetime(self):
        self.source.pending = True

        self.assertEquals(None, self.source.last_crawl)

        self.source.crawled()
        self.assertEquals(False, self.source.pending)
        self.assertNotEquals(None, self.source.last_crawl)

    def test_is_stale_returns_false_when_not_pending(self):
        self.source.pending = False

        self.assertEquals(False, self.source.is_stale())

    def test_is_stale_returns_false_when_pending_and_last_crawl_not_above_threshold(self):
        self.source.pending = True
        self.source.last_crawl = timezone.now()

        self.assertEquals(False, self.source.is_stale())

    def test_is_stale_returns_true_when_pending_and_last_crawl_is_above_threshold(self):
        self.source.pending = True
        self.source.last_crawl = datetime.strptime('2018-05-11 01:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')

        self.assertEquals(True, self.source.is_stale())

    def test_str_returns_name_when_name_is_set(self):
        self.source.name = 'foo'
        self.assertEquals('foo', str(self.source))

    def test_str_returns_none_when_name_is_not_set(self):
        self.assertEquals('', str(self.source))
