from datetime import datetime
import mock
from unittest.mock import patch

from django.utils import timezone
from django.test import TestCase

from core.models.newsitem import NewsItem
from core.models.source import Source
from cli.management.commands import crawl


class CommandTestCase(TestCase):

    feed = {}

    def setUp(self):
        self.feed = {
            'entries': [
                {
                    'title': 'foo',
                    'summary': 'baz',
                    'updated': '2018-12-14T20:00:00+0000',
                    'link': 'https://www.google.com'
                }
            ]
        }

        # retain the original imported packages
        crawl.pika_real = crawl.pika
        crawl.logging_real = crawl.logging
        crawl.NewsItem.exists_real = crawl.NewsItem.exists
        crawl.NewsItem.save_real = crawl.NewsItem.save
        crawl.Source.crawled_real = crawl.Source.crawled
        crawl.Source.crawling_real = crawl.Source.crawling
        crawl.serializers.serialize_real = crawl.serializers.serialize
        crawl.feedparser.parse_real = crawl.feedparser.parse

        # mock pika.BlockingConnection
        self.connection = mock.MagicMock()
        crawl.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        # mock pika.BlockingConnection.channel
        self.channel = mock.MagicMock()
        self.connection.channel = mock.MagicMock(return_value=self.channel)
        # mock ConnectionParameters
        crawl.pika.ConnectionParameters = mock.MagicMock()

        # mock method used by logging
        self.logger = mock.MagicMock()
        crawl.logging.getLogger = mock.MagicMock(return_value=self.logger)

        # mock model methods
        crawl.NewsItem.exists = mock.MagicMock()
        crawl.NewsItem.save = mock.MagicMock()
        crawl.Source.crawled = mock.MagicMock()
        crawl.Source.crawling = mock.MagicMock()

        # mock the serializer that serializes models
        crawl.serializers.serialize = mock.MagicMock()
        # mock the rss feed parser
        crawl.feedparser.parse = mock.MagicMock(return_value=self.feed)

        self.command = crawl.Command()

    def tearDown(self):
        # revert the packages to the original imported
        crawl.pika = crawl.pika_real
        crawl.logging = crawl.logging_real
        crawl.NewsItem.exists = crawl.NewsItem.exists_real
        crawl.NewsItem.save = crawl.NewsItem.save_real
        crawl.Source.crawled = crawl.Source.crawled_real
        crawl.Source.crawling = crawl.Source.crawling_real
        crawl.serializers.serialize = crawl.serializers.serialize_real
        crawl.feedparser.parse = crawl.feedparser.parse_real

    def test_add_arguments_adds_argument_to_command(self):
        parser = mock.MagicMock()
        self.command.add_arguments(parser)
        parser.add_argument.assert_called_once_with('name', nargs='?', type=str)

    def test_handle_exits_when_source_name_option_is_set_and_no_sources_exist(self):
        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='foo')

        # error logged
        self.logger.error.assert_called_once_with('No source(s) found.')
        # no interaction with the queue
        crawl.pika.BlockingConnection.assert_not_called()
        crawl.pika.ConnectionParameters.assert_not_called()
        self.connection.channel.assert_not_called()
        self.channel.queue_declare.assert_not_called()
        # actual crawl not called
        self.command.crawl.assert_not_called()

    def test_handle_exits_when_source_name_option_is_set_and_source_does_not_exist(self):
        source = Source()
        source.name = 'foo'
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='bar')

        # error logged
        self.logger.error.assert_called_once_with('No source(s) found.')
        # no interaction with the queue
        crawl.pika.BlockingConnection.assert_not_called()
        crawl.pika.ConnectionParameters.assert_not_called()
        self.connection.channel.assert_not_called()
        self.channel.queue_declare.assert_not_called()
        # actual crawl not called
        self.command.crawl.assert_not_called()

    def test_handle_exits_when_source_name_option_is_set_and_source_is_inactive(self):
        source = Source()
        source.name = 'foo'
        source.active = False
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='bar')

        # error logged
        self.logger.error.assert_called_once_with('No source(s) found.')
        # no interaction with the queue
        crawl.pika.BlockingConnection.assert_not_called()
        crawl.pika.ConnectionParameters.assert_not_called()
        self.connection.channel.assert_not_called()
        self.channel.queue_declare.assert_not_called()
        # actual crawl not called
        self.command.crawl.assert_not_called()

    def test_handle_crawls_specific_source_when_source_name_option_is_set_and_source_exists_and_is_active(self):
        source = Source()
        source.name = 'foo'
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='foo')

        # no error logged
        self.logger.error.assert_not_called()
        # there is interaction with the queue
        crawl.pika.BlockingConnection.assert_called_once()
        crawl.pika.ConnectionParameters.assert_called_once()
        self.connection.channel.assert_called_once()
        self.channel.queue_declare.assert_called_once()
        # actual crawl called
        self.command.crawl.assert_called_once_with(source, self.channel)

    def test_handle_exits_when_no_source_name_option_is_set_and_no_sources_exist(self):
        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name=None)

        # error logged
        self.logger.error.assert_called_once_with('No source(s) found.')
        # no interaction with the queue
        crawl.pika.BlockingConnection.assert_not_called()
        crawl.pika.ConnectionParameters.assert_not_called()
        self.connection.channel.assert_not_called()
        self.channel.queue_declare.assert_not_called()
        # actual crawl not called
        self.command.crawl.assert_not_called()

    def test_handle_crawls_all_sources_when_no_source_name_option_is_set_and_active_sources_exist(self):
        source = Source()
        source.name = 'foo'
        source.save()

        source = Source()
        source.name = 'bar'
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name=None)

        # no error logged
        self.logger.error.assert_not_called()
        # interaction with the queue
        crawl.pika.BlockingConnection.assert_called_once()
        crawl.pika.ConnectionParameters.assert_called_once()
        self.connection.channel.assert_called_once()
        self.channel.queue_declare.assert_called_once()
        # crawl was called one for each source existing
        self.assertEquals(2, self.command.crawl.call_count)

    def test_handle_crawls_active_sources_when_no_source_name_option_is_set_and_both_active_and_inactive_sources_exist(self):
        source = Source()
        source.name = 'foo'
        source.save()

        source = Source()
        source.name = 'bar'
        source.active = False
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name=None)

        # no error logged
        self.logger.error.assert_not_called()
        # interaction with the queue
        crawl.pika.BlockingConnection.assert_called_once()
        crawl.pika.ConnectionParameters.assert_called_once()
        self.connection.channel.assert_called_once()
        self.channel.queue_declare.assert_called_once()
        # crawl was called one for each source existing
        self.assertEquals(1, self.command.crawl.call_count)

    def test_handle_exits_when_source_is_pending_but_not_stale(self):
        source = Source()
        source.name = 'foo'
        source.pending = True
        source.last_crawl = timezone.now()
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='foo')

        # actual crawl not called
        self.command.crawl.assert_not_called()

    def test_handle_crawls_when_source_is_pending_and_stale(self):
        source = Source()
        source.name = 'foo'
        source.pending = True
        source.last_crawl = datetime.strptime('2018-05-11 01:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')
        source.save()

        self.command.crawl = mock.MagicMock()

        # the method being tested
        self.command.handle(name='foo')

        # actual crawl was called
        self.command.crawl.assert_called_once()

    def test_crawl_exits_when_feed_parse_fails(self):
        # make the parser raise an exception
        crawl.feedparser.parse = mock.MagicMock(side_effect=RuntimeError('foo'))
        self.command = crawl.Command()

        source = Source()
        source.name = 'bar'

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # error logged
        self.logger.error.assert_any_call('Could not crawl \'%s\'.', 'bar')
        # no feed entries so no database transactions them
        crawl.NewsItem.exists.assert_not_called()
        crawl.NewsItem.save.assert_not_called()
        # no serialization and publish to the queue
        crawl.serializers.serialize.assert_not_called()
        self.channel.basic_publish.assert_not_called()
        # source was not crawled, so don't update its last crawl date
        crawl.Source.crawled.assert_not_called()

    def test_crawl_skips_existing_newsitem(self):
        # force exists() to return that the news item already exists to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=True)
        self.command = crawl.Command()

        source = Source()
        source.name = 'bar'

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()
        # existence of news item was performed
        crawl.NewsItem.exists.assert_called_once()
        # feed entry not saved nor published to queue
        crawl.NewsItem.save.assert_not_called()
        crawl.serializers.serialize.assert_not_called()
        self.channel.basic_publish.assert_not_called()
        # mark source as crawled
        crawl.Source.crawled.assert_called_once()

    def test_crawl_sets_newsitem_description_to_summary_value_when_exists(self):
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        # revert mocking the save method of the news item model
        crawl.NewsItem.save = crawl.NewsItem.save_real
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # get the news item inserted into the database
        news_items = NewsItem.objects.all()
        # assert that exists one and that the description has the summary's value
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('baz', news_items[0].description)

    def test_crawl_sets_newsitem_description_to_title_value_when_summary_does_not_exist(self):
        # delete the summary from the fake feed entry
        del(self.feed['entries'][0]['summary'])
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        # revert mocking the save method of the news item model
        crawl.NewsItem.save = crawl.NewsItem.save_real
        # mock the parser to return the fake feed entries
        crawl.feedparser.parse = mock.MagicMock(return_value=self.feed)
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # get the news item inserted into the database
        news_items = NewsItem.objects.all()
        # assert that one exists and the description has the title's value
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('foo', news_items[0].description)

    def test_crawl_sets_newsitem_publish_date_to_published_value_when_published_exists(self):
        # set a new field for the date to the fake feed entry
        self.feed['entries'][0]['published'] = self.feed['entries'][0]['updated']
        self.feed['entries'][0]['updated'] = datetime.now().isoformat()
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        # revert mocking the save method of the news item model
        crawl.NewsItem.save = crawl.NewsItem.save_real
        # mock the parser to return the fake feed entries
        crawl.feedparser.parse = mock.MagicMock(return_value=self.feed)
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # get the news item inserted into the database
        news_items = NewsItem.objects.all()
        # assert that one exists and added_at has the published value
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals(
            datetime.strptime(self.feed['entries'][0]['published'], '%Y-%m-%dT%H:%M:%S%z'),
            news_items[0].added_at
        )

    def test_crawl_sets_newsitem_publish_date_to_updated_value_when_updated_exists(self):
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        # revert mocking the save method of the news item model
        crawl.NewsItem.save = crawl.NewsItem.save_real
        # mock the parser to return the fake feed entries
        crawl.feedparser.parse = mock.MagicMock(return_value=self.feed)
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # get the news item inserted into the database
        news_items = NewsItem.objects.all()
        # assert that one exists and added_at has the updated value
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals(
            datetime.strptime(self.feed['entries'][0]['updated'], '%Y-%m-%dT%H:%M:%S%z'),
            news_items[0].added_at
        )

    def test_crawl_sets_newsitem_publish_date_to_now_when_published_and_updated_do_not_exist(self):
        # delete the updated field from fake feed entry
        del(self.feed['entries'][0]['updated'])
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        # revert mocking the save method of the news item model
        crawl.NewsItem.save = crawl.NewsItem.save_real
        # mock the parser to return the fake feed entries
        crawl.feedparser.parse = mock.MagicMock(return_value=self.feed)
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # get the news item inserted into the database
        news_items = NewsItem.objects.all()
        # assert that one exists and added_at is today
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals(timezone.now().date(), news_items[0].added_at.date())

    def test_crawl_enqueues_classification_of_newsitem_and_marks_source_as_crawled(self):
        # force exists() to return that the news item does not exist to database
        crawl.NewsItem.exists = mock.MagicMock(return_value=False)
        self.command = crawl.Command()

        # create a fake source to crawl
        source = Source()
        source.name = 'bar'
        source.save()

        # ensure that last crawl datetime is not set in before
        self.assertEquals(None, source.last_crawl)

        # the method being tested
        self.command.crawl(source, self.channel)

        # logging the start of the crawling
        self.logger.info.assert_any_call('Crawling \'%s\'...', 'bar')
        # no error logged
        self.logger.error.assert_not_called()

        # the feed entry was saved and enqueued for classification
        crawl.NewsItem.save.assert_called_once()
        self.channel.basic_publish.assert_called_once()
        # the source was marked as pending for crawl
        crawl.Source.crawling.assert_called_once()
        # the source is marked as crawled
        crawl.Source.crawled.assert_called_once()
