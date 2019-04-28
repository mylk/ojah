from datetime import datetime
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from core.models.corpus import Corpus
from core.models.newsitem import NewsItem
from core.models.newsitem_metric import NewsItemMetric
from core.models.source import Source


class NewsItemMetricTestCase(TestCase):

    newsitem_metric = None
    date_range = {
        'date_from': '2018-11-24 00:00:00',
        'date_to': '2018-11-26 00:00:00'
    }

    def setUp(self):
        self.newsitem_metric = NewsItemMetric()

    def test_to_dict_returns_empty_list_when_cursor_with_no_results(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM news_item')
            results = self.newsitem_metric.to_dict(cursor)

        self.assertEquals([], results)

    def test_to_dict_returns_one_dictionary_when_cursor_has_one_result(self):
        source = Source()
        source.id = 1
        source.name = 'foo_source'
        source.save()

        news_item = NewsItem()
        news_item.id = 1
        news_item.title = 'foo'
        news_item.description = 'bar'
        news_item.url = 'https://www.google.com'
        news_item.added_at = '2018-11-23 01:00:00+00:00'
        news_item.source = source
        news_item.published = False
        news_item.score = 1
        news_item.save()

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM news_item')
            result = self.newsitem_metric.to_dict(cursor)

        self.assertEquals(1, len(result))
        self.assertEquals([{
            'id': 1,
            'title': 'foo',
            'description': 'bar',
            'url': 'https://www.google.com',
            'added_at': datetime(2018, 11, 23, 1, 0),
            'source_id': 1,
            'published': False,
            'score': 1
        }], result)

    def test_to_dict_returns_dictionaries_when_cursor_more_than_one_results(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-23 01:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-23 02:00:00+00:00'
        news_item.save()

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM news_item')
            results = self.newsitem_metric.to_dict(cursor)

        self.assertEquals(2, len(results))
        self.assertEquals(dict, type(results[0]))
        self.assertEquals(dict, type(results[1]))

    def test_get_accuracy_returns_empty_list_when_no_newsitems_at_all(self):
        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals([], metrics)

    def test_get_accuracy_does_not_include_unclassified_newsitems(self):
        news_item = NewsItem()
        news_item.score = None
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.score = None
        news_item.published = True
        news_item.added_at = '2018-11-24 02:00:00+00:00'
        news_item.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals([], metrics)

    def test_get_accuracy_returns_empty_list_when_no_newsitems_between_range(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-23 01:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-26 01:00:00+00:00'
        news_item.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals([], metrics)

    def test_get_accuracy_returns_100_percent_when_no_corpora(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals(1, len(metrics))
        self.assertEquals(100, metrics[0]['accuracy'])
        self.assertEquals('2018-11-24', metrics[0]['added_at'])

    def test_get_accuracy_returns_50_percent_when_one_accurate_newsitem_and_one_not_accurate(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 02:00:00+00:00'
        news_item.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals(1, len(metrics))
        self.assertEquals(50, metrics[0]['accuracy'])
        self.assertEquals('2018-11-24', metrics[0]['added_at'])

    def test_get_accuracy_returns_0_percent_when_only_not_accurate_newsitems_exist(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals(1, len(metrics))
        self.assertEquals(0, metrics[0]['accuracy'])
        self.assertEquals('2018-11-24', metrics[0]['added_at'])

    def test_get_accuracy_returns_two_day_statistics_when_newsitems_for_two_days_exist(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-25 01:00:00+00:00'
        news_item.save()

        metrics = self.newsitem_metric.get_accuracy(self.date_range)
        self.assertEquals(2, len(metrics))
        self.assertEquals('2018-11-24', metrics[0]['added_at'])
        self.assertEquals(0, metrics[0]['accuracy'])
        self.assertEquals('2018-11-25', metrics[1]['added_at'])
        self.assertEquals(100, metrics[1]['accuracy'])

    def test_get_accuracy_total_returns_none_when_no_newsitems_at_all(self):
        metrics = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(None, metrics)

    def test_get_accuracy_total_does_not_include_unclassified_newsitems(self):
        news_item = NewsItem()
        news_item.score = None
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.score = None
        news_item.published = True
        news_item.added_at = '2018-11-24 02:00:00+00:00'
        news_item.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(None, accuracy)

    def test_get_accuracy_total_returns_none_when_no_newsitems_between_range(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-23 01:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-26 01:00:00+00:00'
        news_item.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(None, accuracy)

    def test_get_accuracy_total_returns_100_percent_when_no_corpora(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(100, accuracy)

    def test_get_accuracy_total_returns_50_percent_when_one_accurate_newsitem_and_one_not_accurate(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 02:00:00+00:00'
        news_item.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(50.0, accuracy)

    def test_get_accuracy_total_returns_0_percent_when_only_not_accurate_newsitems_exist(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(0.0, accuracy)

    def test_get_accuracy_total_uses_two_day_statistics_when_exist(self):
        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-24 01:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        news_item = NewsItem()
        news_item.score = 1
        news_item.added_at = '2018-11-25 01:00:00+00:00'
        news_item.save()

        accuracy = self.newsitem_metric.get_accuracy_total(self.date_range)
        self.assertEquals(50.0, accuracy)
