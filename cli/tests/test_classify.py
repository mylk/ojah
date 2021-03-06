import mock
from pika.exceptions import ChannelClosed, DuplicateConsumerTag, NoFreeChannels

from django.conf import settings
from django.core import serializers
from django.core.serializers.base import DeserializationError
from django.db.utils import DatabaseError
from django.test import TestCase

from core.models.corpus import Corpus
from core.models.newsitem import NewsItem
from cli.management.commands import classify


class CommandTestCase(TestCase):

    command = None
    thread_classify = None
    thread_train = None
    connection = None
    connection_parameters = None
    channel = None
    logger = None
    serialized_news_item = None
    db_connection = None

    def setUp(self):
        # retain the original imported packages
        classify.serializers_real = classify.serializers

        # mock the tread target methods
        self.thread_classify = mock.MagicMock()
        self.thread_train = mock.MagicMock()
        classify.threading.Thread = mock.MagicMock(side_effect=[self.thread_classify, self.thread_train])

        # mock pika.BlockingConnection
        self.connection = mock.MagicMock()
        classify.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        # mock pika.BlockingConnection.channel
        self.channel = mock.MagicMock()
        self.connection.channel = mock.MagicMock(return_value=self.channel)
        # mock ConnectionParameters
        classify.pika.ConnectionParameters = mock.MagicMock()
        # mock the ORM connection
        self.db_connection = mock.MagicMock()
        classify.connection = self.db_connection

        # mock the classifier
        classify.NaiveBayesClassifier = mock.MagicMock()

        classify.settings.AUTO_PUBLISH = False

        # a fake news item to be used as classification input
        news_item = NewsItem()
        news_item.title = 'foo'
        self.serialized_news_item = serializers.serialize('json', [news_item])

        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.published = 'foo'
        self.serialized_news_item_crap = serializers.serialize('json', [news_item])

        # mock the logger
        self.logger = mock.MagicMock()
        classify.logging.getLogger = mock.MagicMock(return_value=self.logger)

        self.command = classify.Command()

    def tearDown(self):
        # revert the packages to the original imported
        classify.serializers = classify.serializers_real

        # revert class properties to the initial values
        self.command.classifier = None

    def test_handle_fails_when_classifier_training_fails(self):
        # force method to raise an exception
        self.command.get_classifier = mock.MagicMock(side_effect=DatabaseError('foo'))

        # call the method being tested
        self.command.handle()

        # starting of training the classifier and failure are logged
        self.logger.info.assert_called_once_with('Training classifier...')
        self.logger.error.assert_called_once_with('Failed to train the classifier.')
        # threads not started
        self.thread_classify.assert_not_called()
        self.thread_train.assert_not_called()

    def test_handle_starts_training_the_classifier_and_starts_threads(self):
        # mock methods
        channel = mock.MagicMock()
        self.command.get_channel = mock.MagicMock(return_value=channel)
        self.command.get_classifier = mock.MagicMock()

        # call the method being tested
        self.command.handle()

        # method to get channel was called
        self.command.get_channel.assert_called_once()
        # the train queue was purged
        channel.queue_purge.assert_called_with(queue=settings.QUEUE_NAME_TRAIN)
        # starting of training the classifier and success are logged
        self.logger.info.assert_any_call('Training classifier...')
        self.logger.info.assert_any_call('Classifier is ready!')
        # thread started
        self.thread_classify.start.assert_called_once()
        self.thread_train.start.assert_called_once()

    def test_classify_consumer_handles_exception_when_starting_consuming_the_queue(self):
        # mock channel and force to raise an exception
        channel = mock.MagicMock()
        channel.start_consuming = mock.MagicMock(side_effect=ChannelClosed('foo'))
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        # mock the callback called when a message is consumed from the queue
        self.command.classify_decorator = mock.MagicMock()

        # call the method being tested
        self.command.classify_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_CLASSIFY, self.command.classify_decorator)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # error was logged
        self.logger.error.assert_any_call('foo')

    def test_classify_consumer_consumes_the_classify_queue_with_the_classify_decorator(self):
        # mock channel and the method to get a consumer
        channel = mock.MagicMock()
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        self.command.classify_decorator = mock.MagicMock()

        # call the method being tested
        self.command.classify_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_CLASSIFY, self.command.classify_decorator)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # no error was logged
        self.logger.error.assert_not_called()

    def test_train_consumer_handles_exception_when_starting_consuming_the_queue(self):
        # mock channel and force to raise an exception
        channel = mock.MagicMock()
        channel.start_consuming = mock.MagicMock(side_effect=ChannelClosed('foo'))
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        # mock the callback called when a message is consumed from the queue
        self.command.train_callback = mock.MagicMock()

        # call the method being tested
        self.command.train_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_TRAIN, self.command.train_callback)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # error was logged
        self.logger.error.assert_any_call('foo')

    def test_train_consumer_consumes_the_train_queue_with_the_train_callback(self):
        # mock channel and the method to get a consumer
        channel = mock.MagicMock()
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        self.command.train_callback = mock.MagicMock()

        # call the method being tested
        self.command.train_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_TRAIN, self.command.train_callback)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # no error was logged
        self.logger.error.assert_not_called()

    def test_get_channel_handles_exception_when_connecting_to_broker(self):
        # mock connection creation method and force it to raise an exception
        classify.pika.ConnectionParameters = mock.MagicMock(side_effect=ChannelClosed('foo'))

        # call the method being tested
        channel = self.command.get_channel()

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
        # error was logged
        self.logger.error.assert_any_call('foo')
        # no broker channel is returned
        self.assertEquals(None, channel)

    def test_get_channel_returns_channel(self):
        # call the method being tested
        channel = self.command.get_channel()

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)

        # no error was logged
        self.logger.error.assert_not_called()
        # a broker channel is returned
        self.assertNotEquals(None, channel)

    def test_get_consumer_raises_no_exception_and_returns_none_when_channel_is_none(self):
        # just create a fake method to be used as a callback parameter
        classify_decorator = mock.MagicMock()

        # mock the method that creates the channel
        self.command.get_channel = mock.MagicMock(return_value=None)

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_CLASSIFY, classify_decorator)

        # tried to fetch the channel
        self.command.get_channel.assert_called_once()
        # a broker channel is returned
        self.assertEquals(None, channel)

    def test_get_consumer_handles_exception_when_connecting_to_broker(self):
        # mock queue consume method and force it to raise an exception
        self.channel.basic_consume = mock.MagicMock(side_effect=DuplicateConsumerTag('foo'))
        # just create a fake method to be used as a callback parameter
        classify_decorator = mock.MagicMock()

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_CLASSIFY, classify_decorator)

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
        # error was logged
        self.logger.error.assert_any_call('foo')
        # no broker channel is returned
        self.assertEquals(None, channel)

    def test_get_consumer_returns_channel_to_consume_the_classify_queue(self):
        # just create a fake method to be used as a callback parameter
        classify_decorator = mock.MagicMock()
        # a fake channel that get_channel would return
        channel = mock.MagicMock()

        # mock the method that creates the channel
        self.command.get_channel = mock.MagicMock(return_value=channel)

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_CLASSIFY, classify_decorator)

        # the channel was fetched
        self.command.get_channel.assert_called_once()
        # the queue consume method was called
        channel.basic_consume.assert_called_once_with(classify_decorator, queue=settings.QUEUE_NAME_CLASSIFY)
        # no error was logged
        self.logger.error.assert_not_called()
        # a broker channel is returned
        self.assertNotEquals(None, channel)

    def test_get_consumer_returns_channel_to_consume_the_train_queue(self):
        # just create a fake method to be used as a callback parameter
        train_callback = mock.MagicMock()
        # a fake channel that get_channel would return
        channel = mock.MagicMock()

        # mock the method that creates the channel
        self.command.get_channel = mock.MagicMock(return_value=channel)

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_TRAIN, train_callback)

        # the channel was fetched
        self.command.get_channel.assert_called_once()
        # the queue consume method was called
        channel.basic_consume.assert_called_once_with(train_callback, queue=settings.QUEUE_NAME_TRAIN)
        # no error was logged
        self.logger.error.assert_not_called()
        # a broker channel is returned
        self.assertNotEquals(None, channel)

    def test_get_classifier_returns_empty_naive_bayes_classifier_when_no_corpora(self):
        # mock the shuffle list method
        classify.shuffle = mock.MagicMock()
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # call the method being tested
        classifier = self.command.get_classifier()

        # shuffled an empty list of corpora
        classify.shuffle.assert_called_once_with([])
        # a classifier with empty corpora was created
        classify.NaiveBayesClassifier.assert_called_once_with([])
        # the method returned a non-empty result
        self.assertTrue(classifier != None)

    def test_get_classifier_returns_naive_bayes_classifier_with_corpora_when_corpora_exist(self):
        # mock the shuffle list method
        classify.shuffle = mock.MagicMock()
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # create a dummy news item and corpus
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

        # call the method being tested
        classifier = self.command.get_classifier()

        # shuffled the corpora
        classify.shuffle.assert_called_once_with([('foo', 'pos')])
        # a classifier with corpora was created
        classify.NaiveBayesClassifier.assert_called_once_with([('foo', 'pos')])
        # the method returned a non-empty result
        self.assertTrue(classifier != None)

    def test_get_classifier_uses_unique_corpora(self):
        # mock the shuffle list method
        classify.shuffle = mock.MagicMock()
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # create dummy news items and corpora with same title and classification
        for index in range(1, 3):
            news_item = NewsItem()
            news_item.title = 'foo'
            news_item.save()

            corpus = Corpus()
            corpus.news_item = news_item
            corpus.positive = True
            corpus.save()

        # test that two corpora exist
        corpora = Corpus.objects.all()
        self.assertEquals(2, len(corpora))

        # call the method being tested
        classifier = self.command.get_classifier()

        # shuffled the corpora with only one of the identical corpora
        classify.shuffle.assert_called_once_with([('foo', 'pos')])

    def test_get_classifier_uses_corpora_clean_of_stopwords(self):
        # mock the shuffle list method
        classify.shuffle = mock.MagicMock()
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # create dummy news item (having title that contains stopwords) and corpora
        news_item = NewsItem()
        news_item.title = 'when foo then bar'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

        # call the method being tested
        classifier = self.command.get_classifier()

        # shuffled the corpora with only one of the identical corpora
        classify.shuffle.assert_called_once_with([('foo bar', 'pos')])

    def test_classify_decorator_closes_connection(self):
        # mock the consumer callback parameters
        channel = mock.MagicMock()
        method = mock.MagicMock()
        properties = mock.MagicMock()
        body = mock.MagicMock()

        # mock the callback called when a message is consumed from the queue
        self.command.classify_callback = mock.MagicMock()

        # call the method being tested
        self.command.classify_decorator(channel, method, properties, body)

        # the callback is called
        self.command.classify_callback.assert_called_once_with(channel, method, properties, body)
        # connection gets closed after calling the callback
        self.db_connection.close.assert_called_once()

    def test_classify_callback_waits_for_classifier_when_no_trained_classifier_exists(self):
        # mock the time module
        classify.time = mock.MagicMock()
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()
        # nullify any possible trained classifier
        self.command.classifier = None
        # the supposed body of the enqueued item
        body = ''

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), body)

        # un-acknowledged the item got from the queue
        self.channel.basic_nack.assert_called_once()
        # a warning was logged
        self.logger.warning.assert_called_once_with('Classifier was not ready when started to classify.')
        # waited for the classifier to be trained
        classify.time.sleep.assert_called_once()

    def test_classify_callback_handles_exceptions_when_message_is_not_json(self):
        # mock the deserialize method and force it to raise an exception
        classify.serializers.deserialize = mock.MagicMock(side_effect=DeserializationError('foo'))
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()
        # make it look like there is a trained classifier
        self.command.classifier = mock.MagicMock()
        # the supposed body of the enqueued item
        body = ''

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), body)

        # un-acknowledged the item got from the queue
        self.channel.basic_nack.assert_called_once()
        # error was logged
        self.logger.error.assert_called_once_with('Classifier failed to deserialize body.')

    def test_classify_callback_handles_exceptions_when_message_is_not_a_valid_news_item(self):
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()
        # make it look like there is a trained classifier
        self.command.classifier = mock.MagicMock()
        # the supposed body of the enqueued item
        body = '[]'

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), body)

        # un-acknowledged the item got from the queue
        self.channel.basic_nack.assert_called_once()
        # error was logged
        self.logger.error.assert_called_once_with('Classifier failed to get object from deserialized body.')

    def test_classify_callback_handles_exceptions_when_acknowledge_fails(self):
        # mock the deserialize method and force it to raise an exception
        channel = mock.MagicMock()
        channel.basic_ack = mock.MagicMock(side_effect=NoFreeChannels('foo'))
        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()
        # make it look like there is a trained classifier
        self.command.classifier = mock.MagicMock()

        # call the method being tested
        self.command.classify_callback(channel, mock.MagicMock(), mock.MagicMock(), self.serialized_news_item)

        # un-acknowledged the item got from the queue
        channel.basic_nack.assert_called_once()
        # error was logged
        self.logger.error.assert_called_once_with('Classifier could not acknowledge item due to "%s"', 'foo')

    def test_classify_callback_classifies_negative_queue_item_and_saves_on_database(self):
        # make it look like there is a trained classifier that will return a negative class
        self.command.classifier = mock.MagicMock()
        self.command.classifier.classify = mock.MagicMock(return_value='neg')
        # the supposed body of the enqueued item

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), self.serialized_news_item)

        # info was logged that the classification of the news item begins
        self.logger.info.called_once_with('Classifying #1...')
        # the classifier was called with the enqueued news item title
        self.command.classifier.classify.assert_called_once_with('foo')
        # news item is updated in database with the score and publish values
        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('foo', news_items[0].title)
        self.assertEquals(0.00, news_items[0].score)
        self.assertEquals(False, news_items[0].published)
        # un-acknowledged the item got from the queue
        self.channel.basic_ack.assert_called_once()
        # info was logged that the classification was successful
        self.logger.info.called_once_with('Classified #1 "foo" as "neg"!')
        # no error and warning was logged
        self.logger.error.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_classify_callback_classifies_positive_queue_item_and_saves_on_database(self):
        # make it look like there is a trained classifier that will return a negative class
        self.command.classifier = mock.MagicMock()
        self.command.classifier.classify = mock.MagicMock(return_value='pos')

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), self.serialized_news_item)

        # info was logged that the classification of the news item begins
        self.logger.info.called_once_with('Classifying #1...')
        # the classifier was called with the enqueued news item title
        self.command.classifier.classify.assert_called_once_with('foo')
        # news item is updated in database with the score and publish values
        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('foo', news_items[0].title)
        self.assertEquals(1.00, news_items[0].score)
        self.assertEquals(False, news_items[0].published)
        # un-acknowledged the item got from the queue
        self.channel.basic_ack.assert_called_once()
        # info was logged that the classification was successful
        self.logger.info.called_once_with('Classified #1 "foo" as "pos"!')
        # no error and warning was logged
        self.logger.error.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_classify_callback_does_not_auto_publish_news_item_when_auto_publish_is_enabled_but_class_is_negative(self):
        # change the auto-publish setting to true
        classify.settings.AUTO_PUBLISH = True
        # re-initialize the command as we change the imported value above
        self.command = classify.Command()

        # make it look like there is a trained classifier that will return a negative class
        self.command.classifier = mock.MagicMock()
        self.command.classifier.classify = mock.MagicMock(return_value='neg')

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), self.serialized_news_item)

        # info was logged that the classification of the news item begins
        self.logger.info.called_once_with('Classifying #1...')
        # the classifier was called with the enqueued news item title
        self.command.classifier.classify.assert_called_once_with('foo')
        # news item is updated in database with the score and publish values
        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('foo', news_items[0].title)
        self.assertEquals(0.00, news_items[0].score)
        # publish is now set to true, because of the enable auto-publish setting
        self.assertEquals(False, news_items[0].published)
        # un-acknowledged the item got from the queue
        self.channel.basic_ack.assert_called_once()
        # info was logged that the classification was successful
        self.logger.info.called_once_with('Classified #1 "foo" as "neg"!')
        # no error and warning was logged
        self.logger.error.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_classify_callback_auto_publishes_news_item_when_auto_publish_is_enabled_and_class_is_positive(self):
        # change the auto-publish setting to true
        classify.settings.AUTO_PUBLISH = True
        # re-initialize the command as we change the imported value above
        self.command = classify.Command()

        # make it look like there is a trained classifier that will return a negative class
        self.command.classifier = mock.MagicMock()
        self.command.classifier.classify = mock.MagicMock(return_value='pos')

        # call the method being tested
        self.command.classify_callback(self.channel, mock.MagicMock(), mock.MagicMock(), self.serialized_news_item)

        # info was logged that the classification of the news item begins
        self.logger.info.called_once_with('Classifying #1...')
        # the classifier was called with the enqueued news item title
        self.command.classifier.classify.assert_called_once_with('foo')
        # news item is updated in database with the score and publish values
        news_items = NewsItem.objects.all()
        self.assertEquals(1, len(list(news_items)))
        self.assertEquals('foo', news_items[0].title)
        self.assertEquals(1.00, news_items[0].score)
        # publish is now set to true, because of the enable auto-publish setting
        self.assertEquals(True, news_items[0].published)
        # un-acknowledged the item got from the queue
        self.channel.basic_ack.assert_called_once()
        # info was logged that the classification was successful
        self.logger.info.called_once_with('Classified #1 "foo" as "pos"!')
        # no error and warning was logged
        self.logger.error.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_train_callback_purges_queue_and_trains_classifier(self):
        # mock the method that trains the classifier
        self.command.get_classifier = mock.MagicMock()

        # call the method being tested
        self.command.train_callback(self.channel, mock.MagicMock(), None, None)

        # the train queue was purged
        self.channel.queue_purge.assert_called_once_with(queue=settings.QUEUE_NAME_TRAIN)
        # info was logged
        self.logger.info.assert_any_call('train_callback(): Starting training...')
        # the training of the classifier was started
        self.command.get_classifier.assert_called_once()
        # info was logged
        self.logger.info.assert_any_call('train_callback(): Finished training!')

    def test_get_stopwords_returns_not_filtered_stopword(self):
        stopwords = self.command.get_stopwords()
        self.assertTrue('ourselves' in stopwords)

    def test_get_stopwords_does_not_return_filtered_stopword(self):
        stopwords = self.command.get_stopwords()
        self.assertFalse('against' in stopwords)

    def test_reject_queue_item_does_not_handle_exception_when_non_exiting(self):
        # mock the deserialize method and force it to raise an exception
        channel = mock.MagicMock()
        channel.basic_nack = mock.MagicMock()

        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # call the method being tested
        self.command.reject_queue_item(channel, mock.MagicMock())
        # no error was logged
        self.logger.error.assert_not_called()

    def test_reject_queue_handles_exception_while_nack_message(self):
        # mock the deserialize method and force it to raise an exception
        channel = mock.MagicMock()
        channel.basic_nack = mock.MagicMock(side_effect=ChannelClosed('foo'))

        # regenerate the command class being tested as we mocked an extra module above
        self.command = classify.Command()

        # call the method being tested
        self.command.reject_queue_item(channel, mock.MagicMock())
        # error was logged
        self.logger.error.assert_any_call('Classifier could not nack message.')
