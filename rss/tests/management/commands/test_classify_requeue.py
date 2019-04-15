from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import TestCase
import mock
from rss.management.commands import classify_requeue
from core.models.newsitem import NewsItem


class CommandTestCase(TestCase):

    def setUp(self):
        # retain the original imported packages
        classify_requeue.pika_real = classify_requeue.pika
        classify_requeue.logging_real = classify_requeue.logging

        # mock pika.BlockingConnection
        self.connection = mock.MagicMock()
        classify_requeue.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        # mock pika.BlockingConnection.channel
        self.channel = mock.MagicMock()
        self.connection.channel = mock.MagicMock(return_value=self.channel)
        # mock ConnectionParameters
        classify_requeue.pika.ConnectionParameters = mock.MagicMock()

        # mock method used by logging
        self.logger = mock.MagicMock()
        classify_requeue.logging.getLogger = mock.MagicMock(return_value=self.logger)

        self.command = classify_requeue.Command()

    def tearDown(self):
        # revert the packages to the original imported
        classify_requeue.pika = classify_requeue.pika_real
        classify_requeue.logging = classify_requeue.logging_real

    def test_handle_exits_when_no_newsitems(self):
        # the method being tested
        self.command.handle()

        classify_requeue.pika.BlockingConnection.assert_not_called()
        classify_requeue.pika.ConnectionParameters.assert_not_called()
        self.connection.channel.assert_not_called()
        self.channel.queue_declare.assert_not_called()
        self.channel.basic_publish.assert_not_called()
        self.logger.info.assert_called_once_with('All news items are already classified!')

    def test_handle_publishes_when_newsitems_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        # the method being tested
        self.command.handle()

        classify_requeue.pika.BlockingConnection.assert_called_once()
        classify_requeue.pika.ConnectionParameters.assert_called_once()
        self.connection.channel.assert_called_once()
        self.channel.queue_declare.assert_called_once_with(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)
        self.channel.basic_publish.assert_called_once()

        self.logger.info.assert_any_call('Found %s news items that need to be classified.', 1)
        self.logger.info.assert_any_call('Successfully re-queued #%s "%s"!', 1, 'foo')
