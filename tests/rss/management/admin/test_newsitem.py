from django.conf import settings
from django.test import TestCase
import mock
from rss.management.admin import newsitem
from rss.models.corpus import Corpus
from rss.models.newsitem import NewsItem


class NewsItemAdminTestCase(TestCase):

    def setUp(self):
        self.newsitem = newsitem
        self.newsitem.enqueue_corpus_creation_real = self.newsitem.enqueue_corpus_creation
        self.newsitem.enqueue_corpus_creation = mock.MagicMock()

        self.newsitem.pika_real = self.newsitem.pika
        # mock pika.BlockingConnection
        self.connection = mock.MagicMock()
        self.newsitem.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        # mock pika.BlockingConnection.channel
        self.channel = mock.MagicMock()
        self.connection.channel = mock.MagicMock(return_value=self.channel)
        # mock ConnectionParameters
        self.newsitem.pika.ConnectionParameters = mock.MagicMock()

    def tearDown(self):
        self.newsitem.enqueue_corpus_creation = self.newsitem.enqueue_corpus_creation_real
        self.newsitem.pika = self.newsitem.pika_real

    def test_news_item_publish_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.news_item_publish(None, None, query_set)
            success = True
        except:
            pass
        self.assertEquals(True, success)

    def test_news_item_publish_publishes_newsitems_in_query_set(self):
        news_items = NewsItem.objects.all()
        self.assertEquals([], list(news_items))

        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = False
        query_set = [news_item]

        self.newsitem.news_item_publish(None, None, query_set)

        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(news_items))
        self.assertEquals(True, news_items[0].published)

    def test_news_item_unpublish_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.news_item_unpublish(None, None, query_set)
            success = True
        except:
            pass
        self.assertEquals(True, success)

    def test_news_item_unpublish_unpublishes_newsitems_in_query_set(self):
        news_items = NewsItem.objects.all()
        self.assertEquals([], list(news_items))

        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = True
        query_set = [news_item]

        self.newsitem.news_item_unpublish(None, None, query_set)

        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(news_items))
        self.assertEquals(False, news_items[0].published)

    def test_corpus_create_positive_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.corpus_create_positive(None, None, query_set)
            success = True
        except:
            pass
        self.assertEquals(True, success)

    def test_corpus_create_positive_does_not_enqueue_job_to_retrain_classifier_when_no_newsitems_in_query_set(self):
        query_set = []

        self.newsitem.corpus_create_positive(None, None, query_set)
        self.newsitem.enqueue_corpus_creation.assert_not_called()

    def test_corpus_create_positive_creates_positive_corpora_and_enqueues_job_to_retrain_classifier_when_newsitems_in_query_set(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = True
        news_item.save()
        query_set = [news_item]

        self.newsitem.corpus_create_positive(None, None, query_set)

        self.newsitem.enqueue_corpus_creation.assert_called_once()
        corpora = Corpus.objects.all()
        self.assertEquals(1, len(corpora))
        self.assertEquals(True, corpora[0].positive)

    def test_corpus_create_negative_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.corpus_create_negative(None, None, query_set)
            success = True
        except:
            pass
        self.assertEquals(True, success)

    def test_corpus_create_negative_does_not_enqueue_job_to_retrain_classifier_when_no_newsitems_in_query_set(self):
        query_set = []

        self.newsitem.corpus_create_negative(None, None, query_set)
        self.newsitem.enqueue_corpus_creation.assert_not_called()

    def test_corpus_create_negative_creates_negative_corpora_and_enqueues_job_to_retrain_classifier_when_newsitems_in_query_set(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = True
        news_item.save()
        query_set = [news_item]

        self.newsitem.corpus_create_negative(None, None, query_set)

        self.newsitem.enqueue_corpus_creation.assert_called_once()
        corpora = Corpus.objects.all()
        self.assertEquals(1, len(corpora))
        self.assertEquals(False, corpora[0].positive)

    def test_news_item_publish_and_corpus_create_positive_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.news_item_publish_and_corpus_create_positive(None, None, query_set)
            success = True
        except:
            pass
        self.assertEquals(True, success)

    def test_news_item_publish_and_corpus_create_positive_does_not_enqueue_job_to_retrain_classifier_when_no_newsitems_in_query_set(self):
        query_set = []

        self.newsitem.news_item_publish_and_corpus_create_positive(None, None, query_set)
        self.newsitem.enqueue_corpus_creation.assert_not_called()

    def test_news_item_publish_and_corpus_create_positive_publishes_newsitems_and_creates_positive_corpora_when_newsitems_in_query_set(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = False
        news_item.save()

        query_set = [news_item]
        self.newsitem.news_item_publish_and_corpus_create_positive(None, None, query_set)

        self.newsitem.enqueue_corpus_creation.assert_called_once()
        corpora = Corpus.objects.all()
        self.assertEquals(1, len(corpora))
        self.assertEquals(True, corpora[0].positive)
        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(news_items))
        self.assertEquals(True, news_items[0].published)

    def test_news_item_unpublish_and_corpus_create_negative_throws_no_error_when_no_newsitems_in_query_set(self):
        query_set = []
        success = False
        try:
            self.newsitem.news_item_unpublish_and_corpus_create_negative(None, None, query_set)
            success = True
        except:
            pass
        self.assertTrue(success)

    def test_news_item_unpublish_and_corpus_create_negative_does_not_enqueue_job_to_retrain_classifier_when_no_newsitems_in_query_set(self):
        query_set = []

        self.newsitem.news_item_unpublish_and_corpus_create_negative(None, None, query_set)
        self.newsitem.enqueue_corpus_creation.assert_not_called()

    def test_news_item_publish_and_corpus_create_negative_publishes_newsitems_and_creates_negative_corpora_when_newsitems_in_query_set(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.publshed = True
        news_item.score = 1.00
        news_item.save()

        query_set = [news_item]
        self.newsitem.news_item_unpublish_and_corpus_create_negative(None, None, query_set)

        self.newsitem.enqueue_corpus_creation.assert_called_once()
        news_items = NewsItem.object.all()
        self.assertEquals(1, len(news_items))
        self.assertFalse(news_items[0].published)
        corpus = Corpus.object.filter(news_item=news_items[0])
        self.assertNotEquals(None, corpus)
        self.assertFalse(corpus.positive)

    def test_enqueue_corpus_creation_enqueues_job_to_queue(self):
        self.newsitem.enqueue_corpus_creation = self.newsitem.enqueue_corpus_creation_real
        self.newsitem.enqueue_corpus_creation()

        self.newsitem.pika.BlockingConnection.assert_called_once()
        self.newsitem.pika.ConnectionParameters.assert_called_once()
        self.connection.channel.assert_called_once()
        self.channel.queue_declare.assert_called_once_with(queue=settings.QUEUE_NAME_TRAIN, durable=True)
        self.channel.basic_publish.assert_called_once()
