from django.conf import settings
from django.core import serializers
from django.test import TestCase
import mock
from rss.management.commands import classify
from rss.models.corpus import Corpus
from rss.models.newsitem import NewsItem


class CommandTestCase(TestCase):

    command = None
    thread_classify = None
    thread_train = None
    connection = None
    connection_parameters = None
    channel = None
    logger = None
    serialized_news_item = None

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

        # mock the classifier
        classify.NaiveBayesClassifier = mock.MagicMock()

        classify.settings.AUTO_PUBLISH = False

        # a fake news item to be used as classification input
        news_item = NewsItem()
        news_item.title = 'foo'
        self.serialized_news_item = serializers.serialize('json', [news_item])

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
        self.command.get_classifier = mock.MagicMock(side_effect=Exception('foo'))

        # call the method being tested
        self.command.handle()

        # starting of training the classifier and failure are logged
        self.logger.info.assert_called_once_with('Training classifier...')
        self.logger.error.assert_called_once_with('Failed to train the classifier.')
        # threads not started
        self.thread_classify.assert_not_called()
        self.thread_train.assert_not_called()

    def test_handle_starts_training_the_classifier_and_starts_threads(self):
        # mock method
        self.command.get_classifier = mock.MagicMock()

        # call the method being tested
        self.command.handle()

        # starting of training the classifier and success are logged
        self.logger.info.assert_any_call('Training classifier...')
        self.logger.info.assert_any_call('Classifier is ready!')
        # thread started
        self.thread_classify.start.assert_called_once()
        self.thread_train.start.assert_called_once()

    def test_classify_consumer_handles_exception_when_starting_consuming_the_queue(self):
        # mock channel and force to raise an exception
        channel = mock.MagicMock()
        channel.start_consuming = mock.MagicMock(side_effect=Exception('foo'))
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        # mock the callback called when a message is consumed from the queue
        self.command.classify_callback = mock.MagicMock()

        # call the method being tested
        self.command.classify_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_CLASSIFY, self.command.classify_callback)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # error was logged
        self.logger.error.assert_any_call('foo')

    def test_classify_consumer_consumes_the_classify_queue_with_the_classify_callback(self):
        # mock channel and the method to get a consumer
        channel = mock.MagicMock()
        self.command.get_consumer = mock.MagicMock(return_value=channel)
        self.command.classify_callback = mock.MagicMock()

        # call the method being tested
        self.command.classify_consumer()

        # the queue consumer was tried to get fetched
        self.command.get_consumer.assert_called_once_with(settings.QUEUE_NAME_CLASSIFY, self.command.classify_callback)
        # consuming messages from queue was started
        channel.start_consuming.assert_called_once()
        # no error was logged
        self.logger.error.assert_not_called()

    def test_train_consumer_handles_exception_when_starting_consuming_the_queue(self):
        # mock channel and force to raise an exception
        channel = mock.MagicMock()
        channel.start_consuming = mock.MagicMock(side_effect=Exception('foo'))
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

    def test_get_consumer_handles_exception_when_connecting_to_broker(self):
        # mock queue consume method and force it to raise an exception
        self.channel.basic_consume = mock.MagicMock(side_effect=Exception('foo'))
        # just create a fake method to be used as a callback parameter
        classify_callback = mock.MagicMock()

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_CLASSIFY, classify_callback)

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
        # error was logged
        self.logger.error.assert_any_call('foo')
        # no broker channel is returned
        self.assertEquals(None, channel)

    def test_get_consumer_returns_channel_to_consume_the_classify_queue(self):
        # just create a fake method to be used as a callback parameter
        classify_callback = mock.MagicMock()

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_CLASSIFY, classify_callback)

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
        # the queue consume method was called
        self.channel.basic_consume.assert_called_once_with(classify_callback, queue=settings.QUEUE_NAME_CLASSIFY)
        # no error was logged
        self.logger.error.assert_not_called()
        # a broker channel is returned
        self.assertEquals(self.channel, channel)

    def test_get_consumer_returns_channel_to_consume_the_train_queue(self):
        # just create a fake method to be used as a callback parameter
        train_callback = mock.MagicMock()

        # call the method being tested
        channel = self.command.get_consumer(settings.QUEUE_NAME_TRAIN, train_callback)

        # the connection parameters are set correctly
        classify.pika.ConnectionParameters.assert_called_once_with(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
        # the queue consume method was called
        self.channel.basic_consume.assert_called_once_with(train_callback, queue=settings.QUEUE_NAME_TRAIN)
        # no error was logged
        self.logger.error.assert_not_called()
        # a broker channel is returned
        self.assertEquals(self.channel, channel)

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
        self.logger.warn.assert_called_once_with('Classifier was not ready when started to classify.')
        # waited for the classifier to be trained
        classify.time.sleep.assert_called_once()

    def test_classify_callback_handles_exceptions_when_classifying(self):
        # mock the deserialize method and force it to raise an exception
        classify.serializers.deserialize = mock.MagicMock(side_effect=Exception('foo'))
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
        self.logger.error.assert_called_once_with('Could not classify the item due to "foo"')

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
        self.logger.warn.assert_not_called()

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
        self.logger.warn.assert_not_called()

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
        self.logger.warn.assert_not_called()

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
        self.logger.warn.assert_not_called()

    def test_train_callback_purges_queue_and_trains_classifier(self):
        # mock the method that trains the classifier
        self.command.get_classifier = mock.MagicMock()

        # call the method being tested
        self.command.train_callback(self.channel, mock.MagicMock(), None, None)

        # a job from the train queue was acknowledged
        self.channel.basic_ack.assert_called_once()
        # the train queue was purged
        self.channel.queue_purge.assert_called_once_with(queue=settings.QUEUE_NAME_TRAIN)
        # info was logged
        self.logger.info.assert_any_call('train_callback(): Starting training...')
        # the training of the classifier was started
        self.command.get_classifier.assert_called_once()
        # info was logged
        self.logger.info.assert_any_call('train_callback(): Finished training!')
